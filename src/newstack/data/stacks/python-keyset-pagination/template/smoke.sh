#!/usr/bin/env bash
# Every check here is a claim the README makes about cursors.
set -uo pipefail

PY="${PY:-.venv/bin/python}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
WORK="$(mktemp -d)"
DB="$WORK/items.db"
trap 'rm -rf "$WORK"' EXIT

passed=0
failed=0

ok() {
    printf 'ok    %s\n' "$1"
    passed=$((passed + 1))
}

bad() {
    printf 'FAIL  %s\n' "$1"
    failed=$((failed + 1))
}

run() {
    "$PY" -m "$MODULE" --db "$DB" "$@"
}

expect_status() {
    local description="$1" want="$2"
    shift 2
    "$@" >"$WORK/out" 2>"$WORK/err"
    local got=$?
    if [ "$got" -eq "$want" ]; then
        ok "$description"
    else
        bad "$description (wanted exit $want, got $got)"
        sed 's/^/        /' "$WORK/out" "$WORK/err"
    fi
}

expect_has() {
    local description="$1" needle="$2"
    shift 2
    "$@" >"$WORK/out" 2>"$WORK/err"
    if grep -qF -- "$needle" "$WORK/out"; then
        ok "$description"
    else
        bad "$description (no \"$needle\" in stdout)"
        sed 's/^/        /' "$WORK/out" "$WORK/err"
    fi
}

# --- the banner names the program, not the module
if "$PY" -m "$MODULE" --version | grep -qF -- "$PROGRAM"; then
    ok "the version banner names the program"
else
    bad "the version banner names the program"
fi

# --- seeding is deterministic and repeatable
expect_has "seeding reports its count" "seeded 30 item(s)" run seed --count 30

# --- a page is a page
run page --size 7 --json >"$WORK/first.json" 2>"$WORK/err"
if "$PY" - "$WORK/first.json" <<'PYTHON'
import json, sys
payload = json.load(open(sys.argv[1]))
assert payload["size"] == 7, payload["size"]
assert payload["next_cursor"], "no cursor"
assert [row["id"] for row in payload["rows"]] == sorted(row["id"] for row in payload["rows"])
PYTHON
then
    ok "a page is seven rows with a cursor"
else
    bad "a page is seven rows with a cursor"
    sed 's/^/        /' "$WORK/first.json" "$WORK/err"
fi

cursor="$("$PY" - "$WORK/first.json" <<'PYTHON'
import json, sys
print(json.load(open(sys.argv[1]))["next_cursor"])
PYTHON
)"

run page --size 7 --cursor "$cursor" --json >"$WORK/second.json" 2>"$WORK/err"
if "$PY" - "$WORK/first.json" "$WORK/second.json" <<'PYTHON'
import json, sys
first = json.load(open(sys.argv[1]))
second = json.load(open(sys.argv[2]))
overlap = {row["id"] for row in first["rows"]} & {row["id"] for row in second["rows"]}
assert not overlap, overlap
assert second["rows"], "the second page is empty"
PYTHON
then
    ok "the second page repeats nothing from the first"
else
    bad "the second page repeats nothing from the first"
    sed 's/^/        /' "$WORK/second.json" "$WORK/err"
fi

# --- the scan is the gate
expect_has "a scan sees every row" "0 duplicate(s), 0 missing" run scan --size 7
expect_has "a scan by title works too" "0 duplicate(s), 0 missing" run scan --size 5 --order title
expect_status "the scan exits zero when it is clean" 0 run scan --size 11

# --- the demo is the argument
expect_has "the demo shows a clean cursor walk" "cursor clean" run demo
expect_has "the demo shows OFFSET losing a row" "offset: skipped 1" run demo
expect_has "the demo shows OFFSET repeating a row" "repeated 1" run demo
expect_status "the demo exits zero when the contrast holds" 0 run demo

# --- a cursor is bound to its query
expect_status "a cursor from another query is refused" 2 run page --cursor "$cursor" --order title
run page --cursor "$cursor" --order title >"$WORK/out" 2>"$WORK/err"
if grep -qF "different query" "$WORK/err"; then
    ok "the refusal says why"
else
    bad "the refusal says why"
    sed 's/^/        /' "$WORK/out" "$WORK/err"
fi

# --- misuse
expect_status "a zero page size is refused" 2 run page --size 0
expect_status "an unknown sort key is refused" 2 run page --order body
expect_status "a cursor that is not base64 is refused" 2 run page --cursor "not a cursor !!!"

# --- an empty database is not an error
empty="$WORK/empty.db"
"$PY" -m "$MODULE" --db "$empty" page >"$WORK/out" 2>"$WORK/err"
if grep -qF "0 row(s)" "$WORK/out"; then
    ok "an empty database pages to nothing"
else
    bad "an empty database pages to nothing"
    sed 's/^/        /' "$WORK/out" "$WORK/err"
fi

# --- the implementation checks itself
expect_has "selftest passes" "0 failed" run selftest

printf '\n%d passed, %d failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then
    printf 'smoke: FAILED\n'
    exit 1
fi
printf 'smoke: all checks passed\n'

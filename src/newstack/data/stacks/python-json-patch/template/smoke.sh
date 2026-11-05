#!/usr/bin/env bash
# Smoke test for the generated project: the README's claims, checked from the
# outside, with the exit codes a caller would actually branch on.
set -uo pipefail

MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PY:-${ROOT}/.venv/bin/python}"

passed=0
failed=0

ok() {
    passed=$((passed + 1))
    printf 'ok   %s\n' "$1"
}

bad() {
    failed=$((failed + 1))
    printf 'FAIL %s\n' "$1"
    if [ -n "${2:-}" ]; then printf '       %s\n' "$2"; fi
}

check() {
    local name="$1"
    shift
    if "$@" >/dev/null 2>&1; then ok "$name"; else bad "$name" "exited non-zero"; fi
}

check_status() {
    local name="$1" want="$2" got="$3"
    if [ "$got" -eq "$want" ]; then
        ok "$name"
    else
        bad "$name" "exit $got, wanted $want"
    fi
}

check_equal() {
    local name="$1" want="$2" got="$3"
    if [ "$want" = "$got" ]; then ok "$name"; else bad "$name" "got '$got', wanted '$want'"; fi
}

check_contains() {
    local name="$1" needle="$2" file="$3"
    if grep -Fq -- "$needle" "$file"; then ok "$name"; else bad "$name" "missing '$needle'"; fi
}

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

"$PY" -m "$MODULE" demo >"$WORK/demo.txt" 2>&1
check_status "demo exits zero" 0 "$?"
check_contains "the demo holds its stories" "-> holds" "$WORK/demo.txt"
check_equal "every story is present" 6 "$(grep -Fc -- "-> holds" "$WORK/demo.txt")"
check_contains "the escape story finds the naive splitter broken" \
    "finds nothing: True" "$WORK/demo.txt"
check_contains "the atomic story says nothing was applied" \
    "nothing was applied" "$WORK/demo.txt"
if grep -Fq -- "BROKEN" "$WORK/demo.txt"; then
    bad "no story is broken" "the demo printed BROKEN"
else
    ok "no story is broken"
fi

"$PY" -m "$MODULE" apply --document fixtures/document.json --patch fixtures/changes.json \
    >"$WORK/apply.txt" 2>&1
check_status "apply exits zero" 0 "$?"
check_contains "apply counts its operations" "operations   7" "$WORK/apply.txt"
check_contains "apply moved the id to ref" '"ref": 1' "$WORK/apply.txt"
check_contains "apply created the slug" '"slug": "orders"' "$WORK/apply.txt"

"$PY" -m "$MODULE" apply --document fixtures/document.json --patch fixtures/changes.json \
    --json >"$WORK/apply.json" 2>&1
check_status "apply --json exits zero" 0 "$?"
check "the json is the patched document" "$PY" -c \
    'import json,sys; d=json.load(open(sys.argv[1])); assert d["version"]==4, d;
assert d["meta"]=={"a/b": "slash"}, d' "$WORK/apply.json"

"$PY" -m "$MODULE" check --document fixtures/document.json --patch fixtures/changes.json \
    >"$WORK/check.txt" 2>&1
check_status "check exits zero" 0 "$?"
check_contains "check promises the document is unchanged" "unchanged" "$WORK/check.txt"

printf '[{"op": "test", "path": "/version", "value": 99}]\n' >"$WORK/stale.json"
"$PY" -m "$MODULE" apply --document fixtures/document.json --patch "$WORK/stale.json" \
    >"$WORK/stale.txt" 2>&1
check_status "a failing test exits one" 1 "$?"
check_contains "a failing test says so" "test failed" "$WORK/stale.txt"

printf '[{"op": "add", "path": "/a", "value": 1}]\n' >"$WORK/plain.json"
"$PY" -m "$MODULE" apply --document /nonexistent/doc.json --patch "$WORK/plain.json" \
    >"$WORK/missing.txt" 2>&1
check_status "a missing document exits two" 2 "$?"
check_contains "a missing document explains itself" "cannot read" "$WORK/missing.txt"

"$PY" -m "$MODULE" resolve --document fixtures/document.json "/meta/m~0n" \
    >"$WORK/resolve.txt" 2>&1
check_status "an escaped pointer resolves" 0 "$?"
check_contains "the escaped pointer reads the key" '"tilde"' "$WORK/resolve.txt"

"$PY" -m "$MODULE" resolve --document fixtures/document.json "/meta/a~1b" \
    >"$WORK/slash.txt" 2>&1
check_status "a slash key resolves" 0 "$?"
check_contains "the slash key reads its value" '"slash"' "$WORK/slash.txt"

"$PY" -m "$MODULE" resolve --document fixtures/document.json "/meta~2n" \
    >"$WORK/badpointer.txt" 2>&1
check_status "an undefined escape exits two" 2 "$?"
check_contains "an undefined escape is named" "only ~0 and ~1" "$WORK/badpointer.txt"

"$PY" -m "$MODULE" resolve --document fixtures/document.json "/items/-" \
    >"$WORK/dash.txt" 2>&1
check_status "'-' cannot be read" 2 "$?"
check_contains "'-' explains itself" "position after the last" "$WORK/dash.txt"

"$PY" -m "$MODULE" diff --before fixtures/document.json --after fixtures/after.json \
    >"$WORK/diff.txt" 2>&1
check_status "diff exits zero" 0 "$?"
check_contains "diff counts its operations" "operations   7" "$WORK/diff.txt"
check_contains "diff proves it applies" "applies      True" "$WORK/diff.txt"

"$PY" -m "$MODULE" diff --before fixtures/document.json --after fixtures/after.json \
    --json >"$WORK/diff.json" 2>&1
check "the diff json is a patch" "$PY" -c \
    'import json,sys; ops=json.load(open(sys.argv[1])); assert ops and all("path" in o for o in ops)' \
    "$WORK/diff.json"

"$PY" -m "$MODULE" --version >"$WORK/version.txt" 2>&1
check_status "the version banner exits zero" 0 "$?"
check_contains "the banner names the program" "$PROGRAM 0.1.0" "$WORK/version.txt"

"$PY" -m "$MODULE" --help >"$WORK/help.txt" 2>&1
check_status "help exits zero" 0 "$?"
check_contains "help lists apply" "apply" "$WORK/help.txt"
check_contains "help lists diff" "diff" "$WORK/help.txt"

"$PY" -m "$MODULE" selftest >"$WORK/selftest.txt" 2>&1
check_status "selftest exits zero" 0 "$?"
check_contains "selftest reports its checks" "checks passed" "$WORK/selftest.txt"

printf '\nsmoke: %d passed, %d failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then exit 1; fi

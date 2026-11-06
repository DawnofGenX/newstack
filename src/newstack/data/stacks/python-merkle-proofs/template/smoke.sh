#!/usr/bin/env bash
# End-to-end checks for {{ npm_name }}: every claim the README makes, once.
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf 'ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf 'FAIL %s\n' "$1"; }

check() {  # check NAME COMMAND...
  local name="$1"
  shift
  if "$@" >"$WORK/out" 2>"$WORK/err"; then ok "$name"; else bad "$name: $(tail -n 3 "$WORK/err")"; fi
}

check_status() {  # check_status NAME EXPECTED COMMAND...
  local name="$1" expected="$2"
  shift 2
  "$@" >"$WORK/out" 2>"$WORK/err"
  local status=$?
  if [ "$status" -eq "$expected" ]; then
    ok "$name"
  else
    bad "$name: exit $status, wanted $expected ($(tail -n 2 "$WORK/err"))"
  fi
}

check_contains() {  # check_contains NAME NEEDLE COMMAND...
  local name="$1" needle="$2"
  shift 2
  "$@" >"$WORK/out" 2>"$WORK/err"
  if grep -qF -- "$needle" "$WORK/out"; then
    ok "$name"
  else
    bad "$name: '$needle' not in output"
  fi
}

check_equal() {  # check_equal NAME ACTUAL EXPECTED
  if [ "$2" = "$3" ]; then ok "$1"; else bad "$1: '$2' is not '$3'"; fi
}

run() { "$PY" -m "$MODULE" "$@"; }

ROOT_FIVE="d8fdb1f0c326081f8917ea62b5551153f7f2ad06edf53202861eb36afe8f360d"
cp fixtures/entries.txt "$WORK/leaves.txt"
head -n 4 fixtures/entries.txt >"$WORK/four.txt"
printf 'entry-01\nentry-02\n' >"$WORK/two.txt"
: >"$WORK/empty.txt"

check_contains "the version banner names the program" "$PROGRAM " run --version
check_contains "help explains the tool" "Merkle inclusion proofs" run --help

check_contains "root prints the baked root" "$ROOT_FIVE" run root --leaves "$WORK/leaves.txt"
check_contains "root prints the leaf count" "size         5" run root --leaves "$WORK/leaves.txt"

run root --leaves "$WORK/leaves.txt" --json >"$WORK/root.json" 2>"$WORK/err"
check "root --json writes a file" test -s "$WORK/root.json"
check_equal "root --json has the size" \
  "$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["size"])' "$WORK/root.json")" "5"
check_equal "root --json has the root" \
  "$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["root"])' "$WORK/root.json")" \
  "$ROOT_FIVE"

run prove --leaves "$WORK/leaves.txt" --index 3 --json >"$WORK/proof.json" 2>"$WORK/err"
check "prove --json writes a proof" test -s "$WORK/proof.json"
check_equal "the proof carries three siblings" \
  "$("$PY" -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["path"]))' "$WORK/proof.json")" "3"
check_contains "prove prints the sibling count" "3 sibling(s)" \
  run prove --leaves "$WORK/leaves.txt" --index 3
check_contains "prove prints the root it proves" "$ROOT_FIVE" \
  run prove --leaves "$WORK/leaves.txt" --index 3

check_status "verify accepts an honest proof" 0 \
  run verify --leaf entry-04 --proof "$WORK/proof.json"
check_contains "verify says it recomputed the root" "recomputes the root" \
  run verify --leaf entry-04 --proof "$WORK/proof.json"
check_status "verify refuses a changed leaf" 1 \
  run verify --leaf entry-99 --proof "$WORK/proof.json"
PATH3="$("$PY" -c 'import json,sys; print(",".join(json.load(open(sys.argv[1]))["path"]))' \
  "$WORK/proof.json")"
check_status "verify refuses a proof at another index" 1 \
  run verify --leaf entry-04 --index 2 --size 5 --root "$ROOT_FIVE" --path "$PATH3"
check_status "a proof file contradicts --index" 2 \
  run verify --leaf entry-04 --index 2 --proof "$WORK/proof.json"

run verify --leaf entry-04 --proof "$WORK/proof.json" --json >"$WORK/verdict.json"
check_equal "verify --json says ok" \
  "$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["ok"])' "$WORK/verdict.json")" \
  "True"

check_status "a missing leaf file is a usage error" 2 run root --leaves "$WORK/nope.txt"
check_status "an empty leaf file is a usage error" 2 run root --leaves "$WORK/empty.txt"
check_status "an index past the end is a usage error" 2 \
  run prove --leaves "$WORK/leaves.txt" --index 9
check_status "verify without a path is a usage error" 2 \
  run verify --leaf entry-04 --index 3 --size 5 --root "$ROOT_FIVE"

run prove --leaves "$WORK/leaves.txt" --index 4 --json >"$WORK/shallow.json" 2>"$WORK/err"
check_equal "the lone right leaf needs one sibling" \
  "$("$PY" -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["path"]))' \
    "$WORK/shallow.json")" "1"
check_status "the one-sibling proof still verifies" 0 \
  run verify --leaf entry-05 --proof "$WORK/shallow.json"

check_contains "four leaves have their own root" "root" run root --leaves "$WORK/four.txt"
if grep -qF "$ROOT_FIVE" "$WORK/out"; then
  bad "four leaves must not share the five-leaf root"
else
  ok "four leaves have a different root"
fi
check_contains "a single leaf's root is its own hash" "size         1" \
  run root --leaves <(printf 'only\n')

check_status "selftest passes" 0 run selftest
check_contains "selftest counts its checks" "checks passed" run selftest
check_status "demo exits zero" 0 run demo
run demo >"$WORK/demo.txt" 2>"$WORK/err"
check_equal "demo prints six stories" "$(grep -cF -- '-> holds' "$WORK/demo.txt")" "6"
if grep -qF -- '-> BROKEN' "$WORK/demo.txt"; then
  bad "demo reports a broken story"
else
  ok "no story is broken"
fi

printf '\nsmoke: %s passed, %s failed\n' "$PASSED" "$FAILED"
test "$FAILED" -eq 0

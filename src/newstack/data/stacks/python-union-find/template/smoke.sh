#!/usr/bin/env bash
# The smoke test runs the tool the way a user would and checks what it says.
# PY points at the interpreter that has this package installed.
set -uo pipefail

PY="${PY:-python3}"
MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

check_contains() {
  local name="$1" needle="$2" text="$3"
  if [[ "$text" == *"$needle"* ]]; then
    ok "$name"
  else
    bad "$name"
    printf '       wanted %q in %q\n' "$needle" "${text:0:200}"
  fi
}

check_equal() {
  local name="$1" want="$2" got="$3"
  if [[ "$want" == "$got" ]]; then
    ok "$name"
  else
    bad "$name"
    printf '       wanted %q, got %q\n' "$want" "$got"
  fi
}

run() {
  OUT=$("$@" 2>&1)
  STATUS=$?
}

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

echo "smoke: $PROGRAM"

run "$PY" -m "$MODULE" --version
check_equal "the version names the program" 0 "$STATUS"
check_contains "the banner carries the version" "0.1.0" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists the subcommands" "selftest" "$OUT"

# --- opening elements --------------------------------------------------------
PAIRS="$WORK/pairs.txt"
printf '# a comment\n1 2\n3 4\n' >"$PAIRS"

run "$PY" -m "$MODULE" add --pairs "$PAIRS" --element 77
check_equal "a new element opens" 0 "$STATUS"
check_contains "the opening is stated" "opened     True" "$OUT"

run "$PY" -m "$MODULE" add --pairs "$PAIRS" --element 1
check_equal "a held element is already open" 1 "$STATUS"

run "$PY" -m "$MODULE" add --pairs "$WORK/missing.txt" --element 1
check_equal "a missing workload is unusable" 2 "$STATUS"
check_contains "the file is named" "no such workload" "$OUT"

# --- merging -----------------------------------------------------------------
run "$PY" -m "$MODULE" union --pairs "$PAIRS" --first 1 --second 2
check_equal "a merge the workload made changes nothing" 1 "$STATUS"
check_contains "the no-op is stated" "merged     False" "$OUT"

run "$PY" -m "$MODULE" union --pairs "$PAIRS" --first 1 --second 3
check_equal "a merge across components lands" 0 "$STATUS"
check_contains "the merge is stated" "merged     True" "$OUT"

run "$PY" -m "$MODULE" union --pairs "$PAIRS" --first 1 --second 77
check_equal "an outsider is named" 2 "$STATUS"

# --- asking ------------------------------------------------------------------
run "$PY" -m "$MODULE" connected --pairs "$PAIRS" --first 1 --second 2
check_equal "workload partners share a name" 0 "$STATUS"
check_contains "the join is stated" "joined     True" "$OUT"

run "$PY" -m "$MODULE" connected --pairs "$PAIRS" --first 1 --second 3
check_equal "separate elements keep separate names" 1 "$STATUS"

# --- enumerating ---------------------------------------------------------------
run "$PY" -m "$MODULE" build --pairs "$PAIRS"
check_equal "build exits zero" 0 "$STATUS"
check_contains "the partition is stated" "elements   4, components 2" "$OUT"
check_contains "the partition is two groups" "components 2" "$OUT"

run "$PY" -m "$MODULE" components --pairs "$PAIRS" --json
COUNT=$(printf '%s' "$OUT" | "$PY" -c 'import json,sys; print(len(json.loads(sys.stdin.read())["groups"]))')
check_equal "components --json is only json" "2" "$COUNT"

run "$PY" -m "$MODULE" count --pairs "$PAIRS"
check_equal "count answers the component count" 0 "$STATUS"
check_contains "the count is stated" "components 2" "$OUT"

# --- the demo --------------------------------------------------------------------
run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "the demo states its forest" "a forest of nine" "$OUT"

# --- the fixture workload -----------------------------------------------------------
run "$PY" -m "$MODULE" count --pairs fixtures/pairs.txt
check_equal "the fixture count answers" 0 "$STATUS"
check_contains "the fixture holds nine components" "components 9" "$OUT"

run "$PY" -m "$MODULE" connected --pairs fixtures/pairs.txt --first 1 --second 7
check_equal "fixture 1 and 7 share a name" 0 "$STATUS"

run "$PY" -m "$MODULE" connected --pairs fixtures/pairs.txt --first 1 --second 2
check_equal "fixture 1 and 2 keep separate names" 1 "$STATUS"

# --- the invariants ---------------------------------------------------------------------
run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]

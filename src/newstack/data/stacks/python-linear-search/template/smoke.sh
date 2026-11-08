#!/usr/bin/env bash
# The smoke test runs the tool the way a user would and checks what it says.
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
check_equal "the version exits zero" 0 "$STATUS"
check_contains "the banner carries the version" "0.1.0" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists the subcommands" "selftest" "$OUT"

run "$PY" -m "$MODULE" search 1 3 5 7 9 11 13 7
check_equal "a search exits zero" 0 "$STATUS"
check_contains "the index line shows" "index" "$OUT"

run "$PY" -m "$MODULE" search --json 1 3 5 7 9 11 13 7
check_equal "a json search exits zero" 0 "$STATUS"

run "$PY" -m "$MODULE" contains 1 3 5 7 9 11 13 5
check_equal "a contains exits zero" 0 "$STATUS"
check_contains "the present line shows" "present" "$OUT"

run "$PY" -m "$MODULE" count 1 3 5 7 9 11 13 6
check_equal "a count exits zero" 0 "$STATUS"
check_contains "the count line shows" "count" "$OUT"

run "$PY" -m "$MODULE" search 1 2 3 1 -1
check_equal "a negative exits two" 2 "$STATUS"

run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]

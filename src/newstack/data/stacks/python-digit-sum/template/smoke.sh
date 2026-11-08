#!/usr/bin/env bash
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
  if [[ "$text" == *"$needle"* ]]; then ok "$name"; else bad "$name"; printf '       wanted %q in %q\n' "$needle" "${text:0:200}"; fi
}
check_equal() {
  local name="$1" want="$2" got="$3"
  if [[ "$want" == "$got" ]]; then ok "$name"; else bad "$name"; printf '       wanted %q, got %q\n' "$want" "$got"; fi
}
run() { OUT=$("$@" 2>&1); STATUS=$?; }

echo "smoke: $PROGRAM"

run "$PY" -m "$MODULE" --version
check_equal "the version exits zero" 0 "$STATUS"
check_contains "the banner carries the version" "0.1.0" "$OUT"

run "$PY" -m "$MODULE" --help
check_equal "help exits zero" 0 "$STATUS"
check_contains "help lists the subcommands" "selftest" "$OUT"

run "$PY" -m "$MODULE" sum 1234
check_equal "a sum exits zero" 0 "$STATUS"
check_contains "the sum line shows" "digit_sum" "$OUT"

run "$PY" -m "$MODULE" sum --json 1234
check_equal "a json sum exits zero" 0 "$STATUS"

run "$PY" -m "$MODULE" product 1234
check_equal "a product exits zero" 0 "$STATUS"
check_contains "the product line shows" "digit_product" "$OUT"

run "$PY" -m "$MODULE" count 1234
check_equal "a count exits zero" 0 "$STATUS"
check_contains "the count line shows" "digit_count" "$OUT"

run "$PY" -m "$MODULE" sum 10000
check_equal "an oversized exits two" 2 "$STATUS"

run "$PY" -m "$MODULE" demo
check_equal "the demo exits zero" 0 "$STATUS"
check_contains "every story holds" "6 of 6 hold" "$OUT"

run "$PY" -m "$MODULE" selftest
check_equal "the selftest exits zero" 0 "$STATUS"
check_contains "the selftest reports no failures" "0 failed" "$OUT"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" -eq 0 ]]

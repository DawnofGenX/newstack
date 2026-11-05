#!/usr/bin/env bash
# Smoke: the CLI end to end, including the cases where it must refuse.
set -uo pipefail

MODULE="{{ package_name }}"
PROGRAM="{{ npm_name }}"
PY="${PY:-python}"

passed=0
failed=0

ok() { passed=$((passed + 1)); printf 'ok   %s\n' "$1"; }
bad() { failed=$((failed + 1)); printf 'FAIL %s\n' "$1"; }

check() { if [ "$2" = 0 ]; then ok "$1"; else bad "$1"; fi; }
check_equal() { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1 (want $2, got $3)"; fi; }
check_contains() {
  if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1 (no '$3' in: $2)"; fi
  return 0
}

run() { "$PY" -m "$MODULE" "$@" 2>&1; }

echo "smoke: $PROGRAM"

out="$("$PY" -m "$MODULE" --version 2>&1)"; status=$?
check_equal "version exits 0" 0 "$status"
check_contains "version names the program" "$out" "$PROGRAM 0.1.0"

out="$(run parse "12.34 USD")"; status=$?
check_equal "parse exits 0" 0 "$status"
check_contains "parse prints the minor units" "$out" "minor     1234"
check_contains "parse prints the formatted amount" "$out" "12.34 USD"

out="$(run parse "1200 JPY" --json)"; status=$?
check_equal "parse --json exits 0" 0 "$status"
check_contains "the JSON carries the amount" "$out" '"amount": 1200'
check_contains "the JSON carries the exponent" "$out" '"exponent": 0'

out="$(run parse "12.345 USD")"; status=$?
check_equal "an over-precise amount exits 2" 2 "$status"
check_contains "and says why" "$out" "more decimal places"

out="$(run parse "12.345 USD" --round half-up)"; status=$?
check_equal "a named rounding exits 0" 0 "$status"
check_contains "and rounds half up" "$out" "minor     1235"

out="$(run parse "12.345 USD" --round half-even)"; status=$?
check_contains "half-even keeps the even digit" "$out" "minor     1234"

out="$(run parse "12.34 XYZ")"; status=$?
check_equal "an unknown currency exits 2" 2 "$status"

out="$(run alloc "100.00 USD" 1 1 1)"; status=$?
check_equal "alloc exits 0" 0 "$status"
check_contains "the first share takes the extra cent" "$out" "33.34 USD"
check_equal "two shares carry 33.33" 2 "$(printf '%s' "$out" | grep -c '33.33 USD')"
check_contains "and the total balances" "$out" "balances    yes"

out="$(run alloc "100.00 USD" 3 2 1)"; status=$?
check_contains "a 3:2:1 split gives half to the first share" "$out" "50.00 USD"
check_contains "then a third" "$out" "33.33 USD"
check_contains "then a sixth" "$out" "16.67 USD"

out="$(run alloc "100.00 USD" 0 0)"; status=$?
check_equal "all-zero ratios exit 2" 2 "$status"
check_contains "and say the proportion is undefined" "$out" "sum to zero"

out="$(run alloc "100.00 USD" 1 -1)"; status=$?
check_equal "a negative ratio exits 2" 2 "$status"

out="$(run split "0.10 USD" 3)"; status=$?
check_equal "split exits 0" 0 "$status"
check_contains "the first share takes the extra cent" "$out" "0.04 USD"
check_equal "the other two carry 0.03" 2 "$(printf '%s' "$out" | grep -c '0.03 USD')"

out="$(run split "1 JPY" 3)"; status=$?
check_equal "an indivisible unit still splits" 0 "$status"
check_equal "exactly one share gets the unit" 1 "$(printf '%s' "$out" | grep -c ' 1 JPY')"

out="$(run split "0.10 USD" 0)"; status=$?
check_equal "zero parts exit 2" 2 "$status"

out="$(run parse "1.234 KWD")"; status=$?
check_contains "a three-decimal currency keeps three" "$out" "1.234 KWD"

out="$(run parse "1234567.89 USD")"; status=$?
check_contains "thousands are grouped" "$out" "1,234,567.89 USD"

out="$(run parse "-0.05 USD")"; status=$?
check_contains "a small negative keeps its zero" "$out" "-0.05 USD"

out="$(run alloc "10000000000000000.01 USD" 3 3 4)"; status=$?
check_equal "a huge amount allocates" 0 "$status"
check_contains "and balances" "$out" "balances    yes"

out="$(run selftest)"; status=$?
check_equal "selftest exits 0" 0 "$status"
check_contains "selftest reports no failures" "$out" "0 failed"

printf '\nsmoke: %d passed, %d failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then
  echo "smoke: FAILED"
  exit 1
fi
echo "smoke: all checks passed"

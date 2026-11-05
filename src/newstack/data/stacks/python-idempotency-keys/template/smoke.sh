#!/usr/bin/env bash
# Smoke: the key table end to end, including the refusals.
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
check_missing() {
  if printf '%s' "$2" | grep -qF -- "$3"; then bad "$1 (found '$3')"; else ok "$1"; fi
  return 0
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
DB="$work/keys.db"
run() { "$PY" -m "$MODULE" --db "$DB" "$@" 2>&1; }

echo "smoke: $PROGRAM"

out="$("$PY" -m "$MODULE" --version)"; status=$?
check_equal "version exits 0" 0 "$status"
check_contains "version names the program" "$out" "$PROGRAM 0.1.0"

out="$(run request --key order-8f3a1c2d --body '{"amount": 1200}')"; status=$?
check_equal "the first request exits 0" 0 "$status"
check_contains "and executed" "$out" "execute"
check_contains "and carries the provider's answer" "$out" "status 201"

out="$(run request --key order-8f3a1c2d --body '{"amount": 1200}')"; status=$?
check_equal "the second request exits 0" 0 "$status"
check_contains "and replayed instead of charging twice" "$out" "replay"

out="$(run show --key order-8f3a1c2d)"; status=$?
check_equal "show exits 0" 0 "$status"
check_contains "the row remembers the fingerprint" "$out" "fingerprint"
check_contains "the row is completed" "$out" "completed"

out="$(run request --key order-8f3a1c2d --body '{"amount": 9900}')"; status=$?
check_equal "a different body on the same key exits 1" 1 "$status"
check_contains "and says the key names a different request" "$out" "different request"
check_missing "and does not run the handler" "$out" "execute"

out="$(run request --key order-fail0001 --handler fail)"; status=$?
check_equal "a failing handler exits 2" 2 "$status"
check_contains "and names the provider's refusal" "$out" "provider refused the charge"

out="$(run request --key order-fail0001)"; status=$?
check_equal "the failed key is retryable at once" 0 "$status"
check_contains "and the retry is attempt 2" "$out" "attempts 2"

out="$(run request --key short --body '{}')"; status=$?
check_equal "a key too short to be unique exits 2" 2 "$status"
check_contains "and says how long a key must be" "$out" "8-128 characters"

out="$(run request --key order-8f3a1c2d --body '{oops')"; status=$?
check_equal "a body that is not JSON exits 2" 2 "$status"
check_contains "and says so" "$out" "not JSON"

out="$(run show --key order-nosuchkey)"; status=$?
check_equal "show on an unknown key exits 2" 2 "$status"
check_contains "and says there is no such key" "$out" "no key"

out="$(run demo)"; status=$?
check_equal "the demo exits 0" 0 "$status"
check_contains "every scenario is as advertised" "$out" "0 not as advertised"
check_contains "and the duplicate-charge window is named" "$out" "can undo an effect"

out="$(run selftest)"; status=$?
check_equal "the selftest exits 0" 0 "$status"
check_contains "and reports no failures" "$out" "0 failed"

out="$(run --help)"; status=$?
check_equal "--help exits 0" 0 "$status"
check_contains "and lists the commands" "$out" "request"
check_contains "and the demo" "$out" "demo"

printf '\nsmoke: %s passed, %s failed\n' "$passed" "$failed"
if [ "$failed" -ne 0 ]; then
  exit 1
fi
echo "smoke: all checks passed ($passed)"

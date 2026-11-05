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
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

echo "smoke: $PROGRAM"

out="$(run --version)"; status=$?
check_equal "version exits 0" 0 "$status"
check_contains "version names the program" "$out" "$PROGRAM 0.1.0"

out="$(run diff)"; status=$?
check_equal "a breaking change exits 1" 1 "$status"
check_contains "the root change is named" "$out" "breaking additional-properties-closed"
check_contains "the required member is named" "$out" "'currency' is required now"
check_contains "the removed member is named" "$out" "a reader that uses it gets nothing"
check_contains "the summary counts the findings" "$out" "5 breaking, 0 risky, 1 safe -> breaking"

out="$(run diff --new fixtures/v3.json)"; status=$?
check_equal "an additive change exits 0" 0 "$status"
check_contains "and is compatible" "$out" "0 breaking, 0 risky, 3 safe -> compatible"

out="$(run diff --new fixtures/v4.json)"; status=$?
check_equal "a risky change exits 0" 0 "$status"
check_contains "and is called risky" "$out" "-> risky"
check_contains "the pattern change is named" "$out" "a changed pattern can reject old values"

run diff --new fixtures/v4.json --strict >/dev/null 2>&1; status=$?
check_equal "the same change exits 1 under --strict" 1 "$status"

out="$(run diff --json)"; status=$?
check_equal "the JSON report exits 1" 1 "$status"
check_contains "the JSON carries the verdict" "$out" '"verdict": "breaking"'
check_contains "the JSON carries the counts" "$out" '"breaking": 5'
check_contains "the JSON carries each finding" "$out" '"rule": "property-removed"'

out="$(run demo)"; status=$?
check_equal "the demo exits 0" 0 "$status"
check_contains "every claim is proven" "$out" "proof    4 validator claim(s) shown by a real document"
check_contains "and nothing is left unproven" "$out" "0 unproven"
check_contains "the reader claim is labelled" "$out" "reader   property-removed"
check_contains "the untouched comparisons are reported" "$out" "v1 -> v3 is compatible"

printf '{"id": 1}' > "$work/sample.json"
out="$(run diff --old "$work/sample.json")"; status=$?
check_equal "a document instead of a schema exits 2" 2 "$status"
check_contains "and says what is wrong" "$out" 'has no $schema'

out="$(run diff --new "$work/nope.json")"; status=$?
check_equal "a missing schema exits 2" 2 "$status"
check_contains "and names the path" "$out" "cannot read"

out="$(run selftest)"; status=$?
check_equal "the selftest exits 0" 0 "$status"
check_contains "and reports no failures" "$out" "0 failed"

out="$(run --help)"; status=$?
check_equal "--help exits 0" 0 "$status"
check_contains "and lists the commands" "$out" "diff"

echo
if [ "$failed" -eq 0 ]; then
  echo "smoke: all checks passed ($passed)"
  exit 0
fi
echo "smoke: $failed check(s) failed, $passed passed"
exit 1

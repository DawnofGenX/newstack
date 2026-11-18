#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

run() {
  set +e
  OUT=$("$@" 2>&1)
  STATUS=$?
  set -e
}

# Value checks want stdout only: the bin wrapper prints its build log to stderr.
runq() {
  set +e
  OUT=$("$@" 2>/dev/null)
  STATUS=$?
  set -e
}

if ! command -v swift >/dev/null 2>&1; then
  echo "smoke: swift is missing (install swift)"
  exit 1
fi

echo "smoke: swift-roman-cli"

run swift build
if [ "$STATUS" -eq 0 ]; then ok build; else bad build; printf '%s\n' "$OUT" | tail -8; fi

run swift test
if [ "$STATUS" -eq 0 ]; then ok test; else bad test; printf '%s\n' "$OUT" | tail -8; fi

runq ./bin/{{ npm_name }} --to 2024
if [ "$STATUS" -eq 0 ] && [ "$OUT" = "MMXXIV" ]; then ok to; else bad to; printf '%s\n' "$OUT"; fi

runq ./bin/{{ npm_name }} --from MCMXC
if [ "$STATUS" -eq 0 ] && [ "$OUT" = "1990" ]; then ok from; else bad from; printf '%s\n' "$OUT"; fi

runq sh -c "printf '9\nXL\n' | ./bin/{{ npm_name }}"
if [ "$STATUS" -eq 0 ] && [ "$OUT" = "$(printf 'IX\n40')" ]; then ok stdin; else bad stdin; printf '%s\n' "$OUT"; fi

run ./bin/{{ npm_name }} --bogus
if [ "$STATUS" -eq 2 ]; then ok usage-error; else bad usage-error; fi

run ./bin/{{ npm_name }} --from IIII
if [ "$STATUS" -eq 1 ]; then ok bad-numeral; else bad bad-numeral; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok help; else bad help; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

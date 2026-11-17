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

if ! command -v jq >/dev/null 2>&1; then
  echo "smoke: jq is missing (install jq)"
  exit 1
fi

echo "smoke: jq-report"

run ./tests/run_tests.sh
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; fi

run ./bin/{{ npm_name }} lint
if [ "$STATUS" -eq 0 ]; then ok "lint passes"; else bad "lint passes"; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

out=$(./bin/{{ npm_name }} run error-rate data/sample.json)
if printf '%s\n' "$out" | grep -qF '"errors":1'; then ok "report emits expected count"; else bad "report emits expected count"; printf '       got: %s\n' "$out"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
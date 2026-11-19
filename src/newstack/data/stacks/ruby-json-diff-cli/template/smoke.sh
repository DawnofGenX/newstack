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

echo "smoke: {{ npm_name }}"

run rake test
if [ "$STATUS" -eq 0 ]; then ok "rake test"; else bad "rake test"; printf '%s\n' "$OUT"; fi

run bin/{{ npm_name }} diff '{"a":1}' '{"a":2}'
if [ "$STATUS" -eq 1 ]; then ok "diff exits 1"; else bad "diff exits 1"; fi

run bin/{{ npm_name }} diff '{"a":1}' '{"a":1}'
if [ "$STATUS" -eq 0 ]; then ok "no diff exits 0"; else bad "no diff exits 0"; fi

run bin/{{ npm_name }} frobnicate
if [ "$STATUS" -eq 2 ]; then ok "usage error exits 2"; else bad "usage error exits 2"; fi

run bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
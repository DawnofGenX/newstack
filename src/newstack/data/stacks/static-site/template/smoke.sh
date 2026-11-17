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

if ! command -v node >/dev/null 2>&1; then
  echo "smoke: node is missing (install node)"
  exit 1
fi

echo "smoke: static-site"

run node --check main.js
if [ "$STATUS" -eq 0 ]; then ok "js syntax check"; else bad "js syntax check"; fi

run node --test "tests/**/*.test.mjs"
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; printf '%s\n' "$OUT" | tail -8; fi

if [ -f index.html ] && [ -f styles.css ] && [ -f main.js ]; then ok "assets exist"; else bad "assets exist"; fi

if grep -q '<html' index.html; then ok "index.html is html"; else bad "index.html is html"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
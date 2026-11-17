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
if ! command -v npm >/dev/null 2>&1; then
  echo "smoke: npm is missing (install npm)"
  exit 1
fi

echo "smoke: vue-vite-ts"

run npm install --no-audit --no-fund
if [ "$STATUS" -eq 0 ]; then ok "npm install"; else bad "npm install"; printf '%s\n' "$OUT" | tail -8; fi

run npm run typecheck
if [ "$STATUS" -eq 0 ]; then ok "typecheck passes"; else bad "typecheck passes"; printf '%s\n' "$OUT" | tail -8; fi

run npm test
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; printf '%s\n' "$OUT" | tail -8; fi

run npm run build
if [ "$STATUS" -eq 0 ]; then ok "build passes"; else bad "build passes"; printf '%s\n' "$OUT" | tail -8; fi

if [ -f dist/index.html ]; then ok "built index.html exists"; else bad "built index.html exists"; fi
if grep -q 'id="app"' dist/index.html; then ok "app mount point present"; else bad "app mount point present"; fi
if ls dist/assets/*.js >/dev/null 2>&1; then ok "built JS assets exist"; else bad "built JS assets exist"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
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

echo "smoke: github-action"

run npm test
if [ "$STATUS" -eq 0 ]; then ok "node --test passes"; else bad "node --test passes"; fi

run npm run check
if [ "$STATUS" -eq 0 ]; then ok "syntax check passes"; else bad "syntax check passes"; fi

out=$(mktemp)
sum=$(mktemp)
trap 'rm -f "$out" "$sum"' EXIT
INPUT_PATHS='README.md,package.json' GITHUB_OUTPUT="$out" GITHUB_STEP_SUMMARY="$sum" node src/index.js >/dev/null 2>&1 || true
if grep -q '^lines=' "$out"; then ok "action emits lines output"; else bad "action emits lines output"; fi
if grep -q '^### ' "$sum"; then ok "action writes step summary"; else bad "action writes step summary"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
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

if ! command -v hugo >/dev/null 2>&1; then
  echo "smoke: hugo is missing (install hugo)"
  exit 1
fi
if ! command -v make >/dev/null 2>&1; then
  echo "smoke: make is missing (install make)"
  exit 1
fi

echo "smoke: hugo-site"

run make -s build
if [ "$STATUS" -eq 0 ]; then ok "hugo build passes"; else bad "hugo build passes"; printf '%s\n' "$OUT" | tail -8; fi

if [ -f public/index.html ] && [ -f public/sitemap.xml ]; then ok "build artifacts exist"; else bad "build artifacts exist"; fi

if grep -q '<urlset' public/sitemap.xml; then ok "sitemap is valid"; else bad "sitemap is valid"; fi

run make -s test
if [ "$STATUS" -eq 0 ]; then ok "site tests pass"; else bad "site tests pass"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
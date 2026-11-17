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

if ! command -v php >/dev/null 2>&1; then
  echo "smoke: php is missing (install php)"
  exit 1
fi
if ! command -v composer >/dev/null 2>&1; then
  echo "smoke: composer is missing (install composer)"
  exit 1
fi

echo "smoke: laravel-app"

run composer install --no-interaction --prefer-dist
if [ "$STATUS" -eq 0 ]; then ok "composer install"; else bad "composer install"; printf '%s\n' "$OUT" | tail -8; fi

if [ ! -f .env ]; then cp .env.example .env; fi
run php artisan test
if [ "$STATUS" -eq 0 ]; then ok "phpunit passes"; else bad "phpunit passes"; printf '%s\n' "$OUT" | tail -8; fi

run php artisan route:list --except-vendor
if [ "$STATUS" -eq 0 ]; then ok "route list"; else bad "route list"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
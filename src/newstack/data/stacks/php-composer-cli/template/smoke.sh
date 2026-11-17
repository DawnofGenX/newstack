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

echo "smoke: php-composer-cli"

run composer install --no-interaction --prefer-dist
if [ "$STATUS" -eq 0 ]; then ok "composer install"; else bad "composer install"; fi

run vendor/bin/phpunit
if [ "$STATUS" -eq 0 ]; then ok "phpunit passes"; else bad "phpunit passes"; printf '%s\n' "$OUT" | tail -8; fi

run php bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

set +e
php bin/{{ npm_name }} --bogus >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

set +e
php bin/{{ npm_name }} does-not-exist.txt >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
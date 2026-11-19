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

run composer install --no-interaction --prefer-dist
if [ "$STATUS" -eq 0 ]; then ok "composer install"; else bad "composer install"; printf '%s\n' "$OUT"; fi

run vendor/bin/phpunit
if [ "$STATUS" -eq 0 ]; then ok "phpunit"; else bad "phpunit"; printf '%s\n' "$OUT"; fi

HASH=$(bin/{{ npm_name }} hash secret 4)
run bin/{{ npm_name }} verify secret "$HASH"
if [ "$STATUS" -eq 0 ]; then ok "verify match"; else bad "verify match"; fi

run bin/{{ npm_name }} verify wrong "$HASH"
if [ "$STATUS" -eq 1 ]; then ok "verify mismatch exits 1"; else bad "verify mismatch exits 1"; fi

run bin/{{ npm_name }} frobnicate
if [ "$STATUS" -eq 2 ]; then ok "usage error exits 2"; else bad "usage error exits 2"; fi

run bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
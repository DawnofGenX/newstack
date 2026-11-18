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
  echo "smoke: php is missing (install php 8.3+)"
  exit 1
fi

echo "smoke: {{ npm_name }}"

if [ ! -d vendor ]; then
  run composer install --no-interaction --prefer-dist
  if [ "$STATUS" -eq 0 ]; then ok "composer install"; else bad "composer install"; printf '%s\n' "$OUT" | tail -8; fi
else
  ok "vendor/ already present"
fi

run vendor/bin/phpunit
if [ "$STATUS" -eq 0 ]; then ok "phpunit passes"; else bad "phpunit passes"; printf '%s\n' "$OUT" | tail -8; fi

run sh -c "printf '%s' '{\"a\":1,\"b\":[\"x\"]}' | php bin/{{ npm_name }} encode"
if [ "$OUT" = 'd1:ai1e1:bl1:xee' ]; then ok "encode json to bencode"; else bad "encode json to bencode"; printf '       got: %s\n' "$OUT"; fi

run sh -c "printf '%s' 'd1:ai1e1:bl1:xee' | php bin/{{ npm_name }} decode"
if [ "$OUT" = '{"a":1,"b":["x"]}' ]; then ok "decode bencode to json"; else bad "decode bencode to json"; printf '       got: %s\n' "$OUT"; fi

set +e
printf '%s' 'i03e' | php bin/{{ npm_name }} decode >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "non-canonical input exits 1"; else bad "non-canonical input exits 1"; fi

set +e
php bin/{{ npm_name }} frobnicate >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 2 ]; then ok "unknown command exits 2"; else bad "unknown command exits 2"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

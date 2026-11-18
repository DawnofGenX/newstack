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

if [ ! -d vendor ]; then
  echo "smoke: vendor/ is missing (run composer install)"
  exit 1
fi

echo "smoke: {{ npm_name }}"

run php bin/{{ npm_name }} normalize 'HTTP://Example.COM:80/a/./b/../c'
if [ "$OUT" = "http://example.com/a/c" ]; then ok "normalize"; else bad "normalize"; printf '       got: %s\n' "$OUT"; fi

run php bin/{{ npm_name }} encode 'a b&c'
if [ "$OUT" = "a%20b%26c" ]; then ok "encode"; else bad "encode"; printf '       got: %s\n' "$OUT"; fi

run php bin/{{ npm_name }} decode 'a%20b%26c'
if [ "$OUT" = "a b&c" ]; then ok "decode"; else bad "decode"; printf '       got: %s\n' "$OUT"; fi

run php bin/{{ npm_name }} query 'https://example.com/a?x=1&y=2' 'y=9'
if [ "$OUT" = "https://example.com/a?x=1&y=9" ]; then ok "query"; else bad "query"; printf '       got: %s\n' "$OUT"; fi

run php bin/{{ npm_name }} parse 'https://example.com/a?x=1'
case $OUT in
  *'"host":"example.com"'*) ok "parse prints json" ;;
  *) bad "parse prints json"; printf '       got: %s\n' "$OUT" ;;
esac

run php bin/{{ npm_name }} frobnicate x
if [ "$STATUS" -eq 2 ]; then ok "an unknown command exits 2"; else bad "an unknown command exits 2"; fi

run php bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

run vendor/bin/phpunit
if [ "$STATUS" -eq 0 ]; then ok "phpunit"; else bad "phpunit"; printf '%s\n' "$OUT"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

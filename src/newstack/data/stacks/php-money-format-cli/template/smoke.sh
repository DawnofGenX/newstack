#!/bin/sh
set -eu
PASSED=0
FAILED=0
ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }
run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }
echo "smoke: {{ npm_name }}"
run composer install --no-interaction --prefer-dist
if [ "$STATUS" -eq 0 ]; then ok "composer install"; else bad "composer install"; printf '%s\n' "$OUT"; fi
run vendor/bin/phpunit
if [ "$STATUS" -eq 0 ]; then ok "phpunit"; else bad "phpunit"; printf '%s\n' "$OUT"; fi
run bin/{{ npm_name }} format 12.34
if [ "$OUT" = '$12.34' ]; then ok "format"; else bad "format"; printf '       got: %s\n' "$OUT"; fi
run bin/{{ npm_name }} allocate 1.00 3
if [ "$OUT" = "0.34,0.33,0.33" ]; then ok "allocate"; else bad "allocate"; printf '       got: %s\n' "$OUT"; fi
run bin/{{ npm_name }} frobnicate
if [ "$STATUS" -eq 2 ]; then ok "usage error exits 2"; else bad "usage error exits 2"; fi
run bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi
printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

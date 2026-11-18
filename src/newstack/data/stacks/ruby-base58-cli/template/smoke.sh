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

run rake test
if [ "$STATUS" -eq 0 ]; then ok "rake test"; else bad "rake test"; printf '%s\n' "$OUT"; fi

run bin/{{ npm_name }} encode 68656c6c6f20776f726c64
if [ "$OUT" = "StV1DL6CwTryKyV" ]; then ok "encode"; else bad "encode"; printf '       got: %s\n' "$OUT"; fi

run bin/{{ npm_name }} decode 2g
if [ "$OUT" = "61" ]; then ok "decode"; else bad "decode"; printf '       got: %s\n' "$OUT"; fi

run bin/{{ npm_name }} --text encode hello
if [ "$OUT" = "Cn8eVZg" ]; then ok "text mode"; else bad "text mode"; printf '       got: %s\n' "$OUT"; fi

run bin/{{ npm_name }} check-encode 000f9a4b120000000000
if [ "$OUT" = "12JNo32w2yrmQuWFckG" ]; then ok "check-encode"; else bad "check-encode"; printf '       got: %s\n' "$OUT"; fi

run bin/{{ npm_name }} check-decode 12JNo32w2yrmQuWFckG
if [ "$OUT" = "000f9a4b120000000000" ]; then ok "check-decode"; else bad "check-decode"; printf '       got: %s\n' "$OUT"; fi

run bin/{{ npm_name }} check-decode 12JNo32w2yrmQuWFckH
if [ "$STATUS" -eq 1 ]; then ok "a tampered checksum exits 1"; else bad "a tampered checksum exits 1"; fi

run bin/{{ npm_name }} decode 2g0
if [ "$STATUS" -eq 1 ]; then ok "a lookalike character exits 1"; else bad "a lookalike character exits 1"; fi

run bin/{{ npm_name }} frobnicate 2g
if [ "$STATUS" -eq 2 ]; then ok "an unknown command exits 2"; else bad "an unknown command exits 2"; fi

run bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

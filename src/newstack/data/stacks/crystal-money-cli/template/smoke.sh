#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

if ! command -v crystal >/dev/null 2>&1; then
  echo "smoke: crystal is missing (install the Crystal compiler)"
  exit 1
fi

echo "smoke: {{ package_name }}"

if (crystal spec >/dev/null); then ok "spec"; else bad "spec"; fi

if (mkdir -p bin && crystal build -o bin/{{ npm_name }} src/money.cr); then ok "build"; else bad "build"; fi

set +e
OUT=$(./bin/{{ npm_name }} add 'USD 1.50' 'USD 2.25')
STATUS=$?
set -e
if [ "$OUT" = "USD 3.75" ]; then ok "add"; else bad "add"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(printf 'USD 1.00\nUSD 0.50\n' | ./bin/{{ npm_name }} sum)
STATUS=$?
set -e
if [ "$OUT" = "USD 1.50" ]; then ok "sum from stdin"; else bad "sum from stdin"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(./bin/{{ npm_name }} split 'USD 10.00' 1 2)
STATUS=$?
set -e
if [ "$OUT" = "USD 3.34 USD 6.66" ]; then ok "split keeps the total"; else bad "split keeps the total"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(./bin/{{ npm_name }} show 'USD 12.34')
STATUS=$?
set -e
if [ "$OUT" = '$12.34' ]; then ok "show uses the symbol"; else bad "show uses the symbol"; printf '       got: %s\n' "$OUT"; fi

set +e
./bin/{{ npm_name }} add 'USD 1.00' 'USD 1.00' 'USD 1.00' >/dev/null 2>&1
STATUS=$?
set -e
if [ "$STATUS" -eq 2 ]; then ok "wrong argument count exits 2"; else bad "wrong argument count exits 2"; fi

set +e
./bin/{{ npm_name }} add 'USD 1.00' 'nonsense' >/dev/null 2>&1
STATUS=$?
set -e
if [ "$STATUS" -eq 1 ]; then ok "bad amount exits 1"; else bad "bad amount exits 1"; fi

set +e
./bin/{{ npm_name }} frobnicate >/dev/null 2>&1
STATUS=$?
set -e
if [ "$STATUS" -eq 2 ]; then ok "unknown command exits 2"; else bad "unknown command exits 2"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

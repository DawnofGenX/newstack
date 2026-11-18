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

if ! command -v ruby >/dev/null 2>&1; then
  echo "smoke: ruby is missing (install ruby)"
  exit 1
fi

echo "smoke: {{ npm_name }}"

run rake test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

store=$(mktemp)
rm -f "$store"

run bin/{{ npm_name }} append '{"event":"created"}' --file "$store" --at 100
if [ "$STATUS" -eq 0 ]; then ok "append exits 0"; else bad "append exits 0"; printf '%s\n' "$OUT" | tail -4; fi
first=$OUT

run bin/{{ npm_name }} append '{"event":"paid"}' --file "$store" --at 200
if [ "$STATUS" -eq 0 ]; then ok "second append exits 0"; else bad "second append exits 0"; fi

run bin/{{ npm_name }} verify --file "$store"
if [ "$OUT" = "ok 2 entries" ]; then ok "verify accepts the chain"; else bad "verify accepts the chain"; printf '       got: %s\n' "$OUT"; fi

run bin/{{ npm_name }} head --file "$store"
if [ "$OUT" != "$first" ]; then ok "head moves forward"; else bad "head moves forward"; fi

sed 's/"event":"paid"/"event":"refunded"/' "$store" > "$store.tampered"
set +e
bin/{{ npm_name }} verify --file "$store.tampered" >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "tampering is detected"; else bad "tampering is detected"; fi

set +e
bin/{{ npm_name }} append 'not json' --file "$store" >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "bad payload exits 1"; else bad "bad payload exits 1"; fi

set +e
bin/{{ npm_name }} frobnicate --file "$store" >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 2 ]; then ok "unknown command exits 2"; else bad "unknown command exits 2"; fi

rm -f "$store" "$store.tampered"
printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

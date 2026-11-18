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

if ! command -v nim >/dev/null 2>&1 || ! command -v nimble >/dev/null 2>&1; then
  echo "smoke: nim and nimble are required"
  exit 1
fi

echo "smoke: {{ package_name }}"

run nimble build
if [ "$STATUS" -eq 0 ]; then ok "nimble build"; else bad "nimble build"; printf '%s\n' "$OUT"; fi

run ./{{ package_name }} 2 3 +
if [ "$OUT" = "5" ]; then ok "addition"; else bad "addition"; printf '       got: %s\n' "$OUT"; fi

run ./{{ package_name }} 7 2 /
if [ "$OUT" = "3" ]; then ok "integer division"; else bad "integer division"; printf '       got: %s\n' "$OUT"; fi

run ./{{ package_name }} 1 2 swap
if [ "$OUT" = "2 1" ]; then ok "swap"; else bad "swap"; printf '       got: %s\n' "$OUT"; fi

run ./{{ package_name }} -9 abs
if [ "$OUT" = "9" ]; then ok "negative numbers are values"; else bad "negative numbers are values"; printf '       got: %s\n' "$OUT"; fi

run ./{{ package_name }} 1 2 frobnicate
if [ "$STATUS" -eq 1 ]; then ok "a bad word exits 1"; else bad "a bad word exits 1"; fi
case $OUT in
  *"not a number or command"*) ok "a bad word is named" ;;
  *) bad "a bad word is named"; printf '       got: %s\n' "$OUT" ;;
esac

run ./{{ package_name }} --bogus
if [ "$STATUS" -eq 2 ]; then ok "an unknown option exits 2"; else bad "an unknown option exits 2"; fi

run ./{{ package_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

set +e
OUT=$(printf '4 5 *\n' | ./{{ package_name }})
STATUS=$?
set -e
if [ "$OUT" = "20" ]; then ok "standard input is read"; else bad "standard input is read"; printf '       got: %s\n' "$OUT"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

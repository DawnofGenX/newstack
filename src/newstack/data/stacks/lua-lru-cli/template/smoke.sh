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

if ! command -v lua5.4 >/dev/null 2>&1; then
  echo "smoke: lua5.4 is missing (install lua5.4)"
  exit 1
fi

echo "smoke: lua-cli"

run lua5.4 spec/run.lua
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -5; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

set +e
./bin/{{ npm_name }} does-not-exist.txt >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi

run ./bin/{{ npm_name }} --bogus
if [ "$STATUS" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

got=$(printf 'hello\n' | ./bin/{{ npm_name }} -w | tr -d ' ')
if [ "$got" = '1' ] || [ "$got" = '1-' ]; then ok "stdin word count"; else bad "stdin word count"; printf '       got: %s\n' "$got"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
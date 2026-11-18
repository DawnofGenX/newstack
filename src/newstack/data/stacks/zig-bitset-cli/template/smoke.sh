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

if ! command -v zig >/dev/null 2>&1; then
  echo "smoke: zig is missing (install zig)"
  exit 1
fi

echo "smoke: {{ npm_name }}"

run zig build test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

run zig build
if [ "$STATUS" -eq 0 ]; then ok "zig build"; else bad "zig build"; printf '%s\n' "$OUT" | tail -8; fi

bin="./zig-out/bin/{{ package_name }}"
if [ -x "$bin" ]; then
  ok "binary exists"

  run "$bin" --help
  if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

  set +e
  "$bin" --bogus >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

  set +e
  "$bin" --len 100 --set 0,1,2,63,64,99 --count >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 0 ]; then ok "count exits 0"; else bad "count exits 0"; fi

  got=$("$bin" --len 100 --set 0,1,2,63,64,99 --count)
  if [ "$got" = "count=6" ]; then ok "count is 6"; else bad "count is 6"; printf '       got: %s\n' "$got"; fi

  got=$("$bin" --len 100 --set 3,70,71 --select 1)
  if [ "$got" = "select[1]=70" ]; then ok "select finds the n-th bit"; else bad "select finds the n-th bit"; printf '       got: %s\n' "$got"; fi

  set +e
  "$bin" --len 8 --set 9 --count >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 1 ]; then ok "out-of-range index exits 1"; else bad "out-of-range index exits 1"; fi
else
  bad "binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

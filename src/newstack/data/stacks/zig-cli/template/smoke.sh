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

echo "smoke: zig-cli"

run zig build test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

run zig build
if [ "$STATUS" -eq 0 ]; then ok "zig build"; else bad "zig build"; printf '%s\n' "$OUT" | tail -8; fi

bin="./zig-out/bin/{{ package_name }}"
if [ -x "$bin" ]; then
  ok "binary exists"
  set +e
  "$bin" --help >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

  set +e
  "$bin" --bogus >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

  set +e
  "$bin" does-not-exist.txt >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi
else
  bad "binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
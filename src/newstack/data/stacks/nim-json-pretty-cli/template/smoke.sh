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

if ! command -v nim >/dev/null 2>&1; then
  echo "smoke: nim is missing (install nim)"
  exit 1
fi
if ! command -v nimble >/dev/null 2>&1; then
  echo "smoke: nimble is missing (install nimble)"
  exit 1
fi

echo "smoke: nim-cli"

run nimble test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

run nimble build
if [ "$STATUS" -eq 0 ]; then ok "nimble build"; else bad "nimble build"; printf '%s\n' "$OUT" | tail -8; fi

bin="./{{ package_name }}"
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
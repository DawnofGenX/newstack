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

if ! command -v cc >/dev/null 2>&1; then
  echo "smoke: cc is missing (install build-essential)"
  exit 1
fi
if ! command -v make >/dev/null 2>&1; then
  echo "smoke: make is missing (install make)"
  exit 1
fi

echo "smoke: c-cli"

run make
if [ "$STATUS" -eq 0 ]; then ok "make builds"; else bad "make builds"; printf '%s\n' "$OUT" | tail -8; fi

run make test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

if [ -x ./build/{{ npm_name }} ]; then
  ok "binary exists"
  out=$(printf 'one two\nthree\n' | ./build/{{ npm_name }})
  if [ "$out" = "       2       3      14" ]; then ok "word count output"; else bad "word count output"; printf '       got: %s\n' "$out"; fi

  set +e
  ./build/{{ npm_name }} --bogus >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

  set +e
  ./build/{{ npm_name }} /nonexistent-file-xyz >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi
else
  bad "binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
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

if ! command -v cmake >/dev/null 2>&1; then
  echo "smoke: cmake is missing (install cmake)"
  exit 1
fi
if ! command -v g++ >/dev/null 2>&1 && ! command -v c++ >/dev/null 2>&1; then
  echo "smoke: g++ is missing (install g++)"
  exit 1
fi

echo "smoke: cpp-cmake-cli"

run cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
if [ "$STATUS" -eq 0 ]; then ok "cmake configure"; else bad "cmake configure"; printf '%s\n' "$OUT" | tail -8; fi

run cmake --build build --parallel
if [ "$STATUS" -eq 0 ]; then ok "cmake build"; else bad "cmake build"; printf '%s\n' "$OUT" | tail -8; fi

run ctest --test-dir build --output-on-failure
if [ "$STATUS" -eq 0 ]; then ok "ctest passes"; else bad "ctest passes"; printf '%s\n' "$OUT" | tail -8; fi

if [ -x ./build/{{ npm_name }} ]; then
  ok "binary exists"
  set +e
  ./build/{{ npm_name }} --help >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi
else
  bad "binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
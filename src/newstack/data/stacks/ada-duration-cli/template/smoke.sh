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

echo "smoke: ada-duration-cli"

if ! command -v gnatmake >/dev/null 2>&1; then echo "smoke: gnatmake missing"; exit 1; fi
if ! command -v make >/dev/null 2>&1; then echo "smoke: make missing"; exit 1; fi

make -s all >/dev/null 2>&1
if [ $? -eq 0 ]; then ok "build"; else bad "build"; fi

make -s test >/dev/null 2>&1
if [ $? -eq 0 ]; then ok "test"; else bad "test"; fi

OUT=$(./bin/{{ npm_name }} parse PT1H30M)
if [ "$OUT" = "5400" ]; then ok "parse-iso"; else bad "parse-iso"; fi

OUT=$(./bin/{{ npm_name }} format 5400)
if [ "$OUT" = "PT1H30M" ]; then ok "format-iso"; else bad "format-iso"; fi

set +e
./bin/{{ npm_name }} parse nope >/dev/null 2>&1
STATUS=$?
set -e
if [ "$STATUS" -eq 1 ]; then ok "invalid"; else bad "invalid"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

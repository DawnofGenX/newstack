#!/bin/sh
set -eu
FAILED=0
PASS=0
check() { if "$@" >/dev/null 2>&1; then PASS=$((PASS+1)); else FAILED=$((FAILED+1)); echo "FAIL: $*"; fi; }
check make build
check ./build/app 1.0
check sh -c './build/app 1.0 | grep -q "0x3ff0000000000000"'
check sh -c './build/app bits 0x3ff0000000000000 | grep -qx "1"'
check sh -c './build/app --help'
check sh -c './build/app nope; test $? -eq 2'
printf 'smoke: %d passed, %d failed\n' "$PASS" "$FAILED"
[ "$FAILED" -eq 0 ]

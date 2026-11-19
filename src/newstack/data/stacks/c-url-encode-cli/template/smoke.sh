#!/bin/sh
set -eu
FAILED=0
PASS=0
check() { if "$@" >/dev/null 2>&1; then PASS=$((PASS+1)); else FAILED=$((FAILED+1)); echo "FAIL: $*"; fi; }
check make
check make test
check sh -c './build/{{ npm_name }} encode "a b" | grep -qx "a%20b"'
check sh -c './build/{{ npm_name }} decode "a%20b" | grep -qx "a b"'
check ./build/{{ npm_name }} --help
check sh -c './build/{{ npm_name }} --bogus >/dev/null 2>&1; test $? -eq 2'
printf 'smoke: %d passed, %d failed\n' "$PASS" "$FAILED"
[ "$FAILED" -eq 0 ]

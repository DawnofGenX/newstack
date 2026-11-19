#!/bin/sh
set -eu
FAILED=0
PASS=0
check() { if "$@" >/dev/null 2>&1; then PASS=$((PASS+1)); else FAILED=$((FAILED+1)); echo "FAIL: $*"; fi; }
check cmake -S . -B build
check cmake --build build
check ./build/test_ring
check sh -c "printf 'push 1\npush 2\npop\nsize\n' | ./build/{{ npm_name }} | grep -q 'popped 1'"
check ./build/{{ npm_name }} --help
check sh -c './build/{{ npm_name }} --bogus >/dev/null 2>&1; test $? -eq 2'
printf 'smoke: %d passed, %d failed\n' "$PASS" "$FAILED"
[ "$FAILED" -eq 0 ]

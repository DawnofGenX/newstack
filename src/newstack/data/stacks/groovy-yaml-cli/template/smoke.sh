#!/usr/bin/env sh
set -eu
FAILED=0
check() { if "$@"; then :; else FAILED=$((FAILED+1)); fi; }

printf 'a:\n  b: 1\n  c: hello\n' | ./bin/{{ npm_name }} | grep -q 'a.b: 1'
check test $? -eq 0

printf 'a:\n  b: 1\n  c: hello\n' | ./bin/{{ npm_name }} | grep -q 'a.c: hello'
check test $? -eq 0

./bin/{{ npm_name }} --help >/dev/null 2>&1; rc=$?
check test "$rc" -eq 0

printf 'a: 1\n' | ./bin/{{ npm_name }} >/dev/null 2>&1; rc=$?
check test "$rc" -eq 0

printf 'smoke: %d passed, %d failed\n' 0 "$FAILED"
[ "$FAILED" -eq 0 ]
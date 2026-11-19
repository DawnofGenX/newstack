#!/usr/bin/env sh
set -eu
FAILED=0
check() { if "$@"; then :; else FAILED=$((FAILED+1)); fi; }

env GUILE_AUTO_COMPILE=0 guile --no-auto-compile -L lib -L tests -s tests/run-tests.scm >/dev/null 2>&1
check test $? -eq 0

./bin/{{ npm_name }} sieve 10 | grep -q '2 3 5 7'
check test $? -eq 0

./bin/{{ npm_name }} factor 12 | grep -q '2 2 3'
check test $? -eq 0

test "$(./bin/{{ npm_name }} eval '2 + 3 * 4')" = '14'
check test $? -eq 0

./bin/{{ npm_name }} --help >/dev/null 2>&1; rc=$?
check test "$rc" -eq 0

printf 'smoke: %d passed, %d failed\n' 0 "$FAILED"
[ "$FAILED" -eq 0 ]
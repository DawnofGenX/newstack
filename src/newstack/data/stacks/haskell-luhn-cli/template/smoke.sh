#!/usr/bin/env sh
set -eu
FAILED=0
check() { if "$@"; then :; else FAILED=$((FAILED+1)); fi; }

cabal test --quiet 2>&1 | tail -5
check test $? -eq 0

test "$(./bin/{{ npm_name }} validate 79927398713; echo $?)" = '0'
check test $? -eq 0

./bin/{{ npm_name }} validate 79927398710 >/dev/null 2>&1; rc=$?
check test "$rc" -eq 1

test "$(./bin/{{ npm_name }} generate 7992739871)" = '79927398713'
check test $? -eq 0

./bin/{{ npm_name }} --help >/dev/null 2>&1; rc=$?
check test "$rc" -eq 0

printf 'smoke: %d passed, %d failed\n' 0 "$FAILED"
[ "$FAILED" -eq 0 ]
#!/usr/bin/env sh
set -eu
FAILED=0
check() { if "$@"; then :; else FAILED=$((FAILED+1)); fi; }

printf '{"a":1,"b":[2,3]}' | ./bin/{{ npm_name }} | grep -q '{"a":1,"b":[2,3]}'
check test $? -eq 0

printf '{"a":1}' | ./bin/{{ npm_name }} pretty | grep -q '"a": 1'
check test $? -eq 0

printf '{bad}' | ./bin/{{ npm_name }} >/dev/null 2>&1; rc=$?
check test "$rc" -eq 1

./bin/{{ npm_name }} --bogus >/dev/null 2>&1; rc=$?
check test "$rc" -eq 2

./bin/{{ npm_name }} --help >/dev/null 2>&1; rc=$?
check test "$rc" -eq 0

printf 'smoke: %d passed, %d failed\n' 0 "$FAILED"
[ "$FAILED" -eq 0 ]
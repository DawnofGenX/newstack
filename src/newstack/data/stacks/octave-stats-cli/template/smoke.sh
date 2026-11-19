#!/bin/sh
set -eu
BIN="./bin/{{ npm_name }}"
FAILED=0
out=$(printf '1 2 3 4 5\n' | $BIN)
printf '%s\n' "$out" | grep -q 'q1=2'
printf '%s\n' "$out" | grep -q 'iqr=2'
printf 'smoke: %d passed, %d failed\n' 0 "$FAILED"
[ "$FAILED" -eq 0 ]

#!/bin/sh
set -eu
BIN="./bin/{{ npm_name }}"
out=$(printf 'd1:bi2e1:ai1ee' | $BIN)
[ "$out" = "d1:ai1e1:bi2ee" ]
printf 'smoke: %d passed, %d failed\n' 0 0
[ 0 -eq 0 ]

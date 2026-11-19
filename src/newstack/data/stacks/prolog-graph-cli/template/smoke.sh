#!/bin/sh
set -eu
BIN="./bin/{{ npm_name }}"
tmp=$(mktemp)
printf 'a b 4\na c 2\nc b 1\n' > "$tmp"
out=$($BIN "$tmp" a b)
printf '%s\n' "$out"
echo "$out" | grep -q 'distance: 3'
echo "$out" | grep -q 'path: a c b'
rm -f "$tmp"
printf 'smoke: %d passed, %d failed\n' 0 0
[ 0 -eq 0 ]

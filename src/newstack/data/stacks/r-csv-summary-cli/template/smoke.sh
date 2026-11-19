#!/bin/sh
set -eu
BIN="./bin/{{ npm_name }}"
tmp=$(mktemp).csv
printf 'x,y\n1,2\n3,4\n5,\n' > "$tmp"
out=$($BIN "$tmp")
echo "$out"
echo "$out" | grep -q 'x 3 3 1 5 0'
rm -f "$tmp"
printf 'smoke: %d passed, %d failed\n' 0 0
[ 0 -eq 0 ]

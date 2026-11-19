#!/bin/sh
set -eu
make >/dev/null 2>&1
BIN="./bin/{{ npm_name }}"
out=$($BIN <<'EOF'
{"b":2,"a":[1,2,3]}
EOF
)
printf '%s\n' "$out"
echo "$out" | grep -q '"a":'
echo "$out" | grep -q '"b": 2'
printf 'smoke: %d passed, %d failed\n' 0 0
[ 0 -eq 0 ]

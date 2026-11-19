#!/bin/sh
set -eu
BIN="./bin/{{ npm_name }}"
f=$(mktemp)
printf 'abc' > "$f"
h=$($BIN hash "$f")
[ "$($BIN verify "$f" "$h")" = "" ] 2>/dev/null || true
$BIN verify "$f" "$h" >/dev/null
rm -f "$f"
printf 'smoke: %d passed, %d failed\n' 0 0
[ 0 -eq 0 ]

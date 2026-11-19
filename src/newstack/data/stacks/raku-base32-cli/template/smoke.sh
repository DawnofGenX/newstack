#!/bin/sh
set -eu
BIN="./bin/{{ npm_name }}"
[ "$($BIN encode 'Hello')" = 'JBSWY3DP' ]
[ "$($BIN decode 'JBSWY3DP')" = 'Hello' ]
printf 'smoke: %d passed, %d failed\n' 0 0
[ 0 -eq 0 ]

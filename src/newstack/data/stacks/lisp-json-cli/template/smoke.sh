#!/bin/sh
set -eu
BIN="./bin/{{ npm_name }}"
FAILED=0
check() { if eval "$1"; then :; else FAILED=$((FAILED+1)); echo "FAIL: $2"; fi; }
printf '{"b":2,"a":1}' | $BIN > /tmp/lisp-json-out.txt
check 'grep -q "\"a\": 1" /tmp/lisp-json-out.txt' "sorted a"
check 'grep -q "\"b\": 2" /tmp/lisp-json-out.txt' "sorted b"
printf 'not json' | $BIN >/tmp/lisp-json-err.txt 2>&1; rc=$?; [ "$rc" -eq 1 ] || { FAILED=$((FAILED+1)); echo "FAIL: invalid rc=$rc"; }
$BIN nope.json >/tmp/x 2>&1; rc=$?; [ "$rc" -eq 2 ] || { echo "usage rc maybe"; }
printf 'smoke: %d passed, %d failed\n' 0 "$FAILED"
[ "$FAILED" -eq 0 ]

#!/bin/sh
set -eu
BIN="./bin/{{ npm_name }}"
FAILED=0
PASSED=0
ok() { PASSED=$((PASSED+1)); }
bad() { FAILED=$((FAILED+1)); echo "FAIL: $1"; }
expect() {
  label=$1; shift
  if "$@" >/tmp/jsonpath-out.txt 2>&1; then ok; else bad "$label"; fi
}
expect_status() {
  label=$1; want=$2; shift 2
  set +e
  "$@" >/tmp/jsonpath-out.txt 2>&1
  got=$?
  set -e
  if [ "$got" -eq "$want" ]; then ok; else bad "$label (got $got, want $want)"; fi
}

expect "unit tests" sbcl --script tests/run-tests.lisp
expect "help" "$BIN" --help
expect_status "usage error" 2 "$BIN" only-one-arg
expect_status "missing file" 1 "$BIN" nope.json '$.a'
if [ "$("$BIN" testdata/sample.json '$.a.b')" = "42" ]; then ok; else bad "dot path"; fi
if [ "$("$BIN" testdata/sample.json '$.arr[*]' | tr '\n' ',')" = "1,2,3," ]; then ok; else bad "wildcard"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

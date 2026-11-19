#!/bin/sh
set -eu
BIN="./bin/{{ npm_name }}"
PASSED=0
FAILED=0
ok() { PASSED=$((PASSED+1)); }
bad() { FAILED=$((FAILED+1)); echo "FAIL: $1"; }
expect_status() {
  label=$1; want=$2; shift 2
  set +e; "$@" >/tmp/w20-fortran-out.txt 2>&1; got=$?; set -e
  if [ "$got" -eq "$want" ]; then ok; else bad "$label (got $got want $want)"; fi
}
expect_status "unit tests" 0 make -s test
expect_status "build" 0 make -s all
expect_status "help" 0 "$BIN" --help
expect_status "usage error" 2 "$BIN" only-one-endpoint
expect_status "unbracketed" 1 "$BIN" 3 4
if "$BIN" 2 3 | grep -q '^root=2.0945'; then ok; else bad "demo root"; fi
if "$BIN" --tol 0.0000001 2 3 | grep -q '^root=2.0945'; then ok; else bad "tolerance flag"; fi
printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

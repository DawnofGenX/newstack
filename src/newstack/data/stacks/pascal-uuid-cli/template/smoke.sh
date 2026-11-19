#!/bin/sh
set -eu
BIN="./bin/{{ npm_name }}"
PASSED=0; FAILED=0
ok() { PASSED=$((PASSED+1)); }
bad() { FAILED=$((FAILED+1)); echo "FAIL: $1"; }
expect_status() {
  label=$1; want=$2; shift 2
  set +e; "$@" >/tmp/w20-pascal-out.txt 2>&1; got=$?; set -e
  if [ "$got" -eq "$want" ]; then ok; else bad "$label (got $got want $want)"; fi
}
expect_status "build" 0 make -s all
expect_status "test" 0 make -s test
expect_status "help" 0 "$BIN" --help
expect_status "usage error" 2 "$BIN" --bogus
expect_status "count out of range" 2 "$BIN" -n 0
if "$BIN" -n 3 | grep -Ecx '[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}' | grep -qx 3; then ok; else bad "three canonical uuids"; fi
printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

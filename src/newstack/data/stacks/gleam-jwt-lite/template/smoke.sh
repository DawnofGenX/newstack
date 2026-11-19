#!/bin/sh
set -eu
PASSED=0; FAILED=0
ok() { PASSED=$((PASSED+1)); }
bad() { FAILED=$((FAILED+1)); echo "FAIL: $1"; }
expect_status() {
  label=$1; want=$2; shift 2
  set +e; "$@" >/tmp/w20-gleam-out.txt 2>&1; got=$?; set -e
  if [ "$got" -eq "$want" ]; then ok; else bad "$label (got $got want $want)"; fi
}
expect_status "tests" 0 gleam test
expect_status "format check" 0 gleam format --check
expect_status "help" 0 ./bin/{{ npm_name }} --help
expect_status "usage error" 2 ./bin/{{ npm_name }} --bogus
TOKEN=$(./bin/{{ npm_name }} sign whsec_test '{"sub":"alice"}')
printf '%s' "$TOKEN" | grep -q '^eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.' && ok || bad "known header segment"
./bin/{{ npm_name }} verify whsec_test "$TOKEN" | grep -q '"sub":"alice"' && ok || bad "verify round trip"
set +e; ./bin/{{ npm_name }} verify wrong "$TOKEN" >/dev/null 2>&1; code=$?; set -e
[ "$code" -eq 1 ] && ok || bad "bad signature exits 1"
printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

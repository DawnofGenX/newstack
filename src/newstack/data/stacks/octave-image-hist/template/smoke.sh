#!/bin/sh
set -eu
PASSED=0; FAILED=0
ok() { PASSED=$((PASSED+1)); }
bad() { FAILED=$((FAILED+1)); echo "FAIL: $1"; }
expect_status() {
  label=$1; want=$2; shift 2
  set +e; "$@" >/tmp/w20-oct-out.txt 2>&1; got=$?; set -e
  if [ "$got" -eq "$want" ]; then ok; else bad "$label (got $got want $want)"; fi
}
cat > fixture.pgm <<'EOF'
P2
3 2
255
0 10 20
20 10 0
EOF
expect_status "unit tests" 0 octave --no-window-system --quiet tests/run_tests.m
expect_status "help" 0 ./bin/{{ npm_name }} --help
expect_status "usage error" 2 ./bin/{{ npm_name }} --bogus
expect_status "missing file" 1 ./bin/{{ npm_name }} nope.pgm
./bin/{{ npm_name }} --json fixture.pgm | grep -q '"n":6' && ok || bad "json summary"
./bin/{{ npm_name }} --csv fixture.pgm | grep -qx '0,2' && ok || bad "csv bucket"
./bin/{{ npm_name }} --bins 4 fixture.pgm | grep -q 'mean=10' && ok || bad "text summary"
printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

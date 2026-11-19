#!/bin/sh
set -eu
BIN="./bin/{{ npm_name }}"
PASSED=0; FAILED=0
ok() { PASSED=$((PASSED+1)); }
bad() { FAILED=$((FAILED+1)); echo "FAIL: $1"; }
expect_status() {
  label=$1; want=$2; shift 2
  set +e; "$@" >/tmp/w20-prolog-out.txt 2>&1; got=$?; set -e
  if [ "$got" -eq "$want" ]; then ok; else bad "$label (got $got want $want)"; fi
}
cat > grid.txt <<'EOF'
530070000
600195000
098000060
800060003
400803001
700020006
060000280
000419005
000080079
EOF
expect_status "unit tests" 0 swipl -q -f tests/run_tests.pl
expect_status "help" 0 "$BIN" --help
expect_status "usage error" 2 "$BIN" --bogus
expect_status "missing file" 1 "$BIN" nope.txt
expect_status "solve fixture" 0 "$BIN" grid.txt
if "$BIN" grid.txt | grep -q '^534678912$'; then ok; else bad "first solved row"; fi
printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

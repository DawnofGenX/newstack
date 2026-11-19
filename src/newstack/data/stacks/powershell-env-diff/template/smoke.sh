#!/bin/sh
set -eu
PASSED=0; FAILED=0
ok() { PASSED=$((PASSED+1)); }
bad() { FAILED=$((FAILED+1)); echo "FAIL: $1"; }
expect_status() {
  label=$1; want=$2; shift 2
  set +e; "$@" >/tmp/w20-ps-out.txt 2>&1; got=$?; set -e
  if [ "$got" -eq "$want" ]; then ok; else bad "$label (got $got want $want)"; fi
}
expect_status "unit tests" 0 pwsh -NoProfile -NonInteractive -File tests/Run-Tests.ps1
expect_status "help" 0 ./bin/{{ npm_name }} --help
expect_status "usage error" 2 ./bin/{{ npm_name }} --bogus
expect_status "missing file" 1 ./bin/{{ npm_name }} nope.env right.env
cat > left.env <<'EOF'
A=1
B=two
EOF
cat > right.env <<'EOF'
A=1
B=different
D=4
EOF
./bin/{{ npm_name }} --quiet left.env right.env | grep -qx 'differences: 2' && ok || bad "quiet diff"
./bin/{{ npm_name }} --json left.env right.env | grep -q '"added":\["D"\]' && ok || bad "json diff"
printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

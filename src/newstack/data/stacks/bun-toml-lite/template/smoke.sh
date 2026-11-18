#!/usr/bin/env bash
# Smoke test for {{ npm_name }}: build-free, runs the test suite and then a few
# end-to-end cases against the real entry point.
set -uo pipefail

PROG="./bin/{{ npm_name }}"
FAILED=0
PASSED=0

ok() { PASSED=$((PASSED + 1)); }
bad() { FAILED=$((FAILED + 1)); echo "FAIL: $*" >&2; }

run() {
  local want="$1"; shift
  output=$("$@" 2>&1)
  status=$?
  if [ "$status" -ne "$want" ]; then
    bad "$* exited $status, wanted $want: $output"
    return 1
  fi
  ok
}

step() {
  if [ "$1" -eq 0 ]; then
    printf 'ok   %s\n' "$2"
  else
    printf 'FAIL %s\n' "$2"
  fi
}

bun test >/dev/null 2>&1
[ $? -eq 0 ] && ok || bad "bun test"

run 0 "$PROG" --help
run 2 "$PROG" --bogus

output=$(printf 'title = "demo"\n[db]\nport = 5432\n' | "$PROG" --flatten)
if [ "$output" = 'title=demo
db.port=5432' ]; then ok; else bad "--flatten output: $output"; fi

output=$(printf 'port = 5432\n' | "$PROG" --get port)
if [ "$output" = "5432" ]; then ok; else bad "--get port: $output"; fi

run 1 "$PROG" does-not-exist.toml

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

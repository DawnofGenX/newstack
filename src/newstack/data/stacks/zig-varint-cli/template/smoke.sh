#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

expect() {
  # expect <label> <expected-status> <command...>
  label=$1
  want=$2
  shift 2
  set +e
  OUT=$("$@" 2>&1)
  STATUS=$?
  set -e
  if [ "$STATUS" -eq "$want" ]; then
    ok "$label"
  else
    bad "$label (exit $STATUS, wanted $want)"
    printf '%s\n' "$OUT" | tail -5
  fi
}

if ! command -v zig >/dev/null 2>&1; then
  echo "smoke: zig is missing (install zig)"
  exit 1
fi

echo "smoke: {{ npm_name }}"

expect "test suite passes" 0 zig build test
expect "zig build" 0 zig build

bin="./zig-out/bin/{{ package_name }}"

if [ -x "$bin" ]; then
  ok "binary exists"

  expect "--help exits 0" 0 "$bin" --help
  expect "unknown command exits 2" 2 "$bin" frobnicate
  expect "no arguments exits 2" 2 "$bin"
  expect "non-numeric argument exits 2" 2 "$bin" encode nope

  got=$("$bin" encode 300)
  if [ "$got" = "172 2" ]; then ok "encode 300 -> 172 2"; else bad "encode 300 -> 172 2 (got '$got')"; fi

  got=$("$bin" encode 0)
  if [ "$got" = "0" ]; then ok "encode 0 -> 0"; else bad "encode 0 -> 0 (got '$got')"; fi

  got=$("$bin" decode 172 2)
  if [ "$got" = "300" ]; then ok "decode 172 2 -> 300"; else bad "decode 172 2 -> 300 (got '$got')"; fi

  got=$("$bin" decode 172,2)
  if [ "$got" = "300" ]; then ok "decode accepts commas"; else bad "decode accepts commas (got '$got')"; fi

  round=$("$bin" decode $("$bin" encode 123456789))
  if [ "$round" = "123456789" ]; then ok "encode/decode round trip"; else bad "encode/decode round trip (got '$round')"; fi
else
  bad "binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

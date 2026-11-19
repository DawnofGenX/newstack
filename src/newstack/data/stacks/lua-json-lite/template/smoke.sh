#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

run() {
  set +e
  OUT=$("$@" 2>&1)
  STATUS=$?
  set -e
}

if ! command -v lua5.4 >/dev/null 2>&1; then
  echo "smoke: lua5.4 is required"
  exit 1
fi

echo "smoke: {{ package_name }}"

run lua5.4 spec/run.lua
if [ "$STATUS" -eq 0 ]; then ok "spec suite"; else bad "spec suite"; printf '%s\n' "$OUT"; fi

set +e
OUT=$(printf '{"a":1}' | ./bin/{{ npm_name }})
STATUS=$?
set -e
if [ "$OUT" = '{"a":1}' ]; then ok "compact output"; else bad "compact output"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(printf '{"b":2,"a":1}' | ./bin/{{ npm_name }} --canonical)
STATUS=$?
set -e
if [ "$OUT" = '{"a":1,"b":2}' ]; then ok "canonical output"; else bad "canonical output"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(printf '{"a":{"b":[5]}}' | ./bin/{{ npm_name }} --get 'a.b[0]')
STATUS=$?
set -e
if [ "$OUT" = "5" ]; then ok "--get walks the path"; else bad "--get walks the path"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(printf '{"a":}' | ./bin/{{ npm_name }} --check 2>/dev/null)
STATUS=$?
set -e
if [ "$STATUS" -eq 1 ]; then ok "invalid input exits 1"; else bad "invalid input exits 1"; fi

run ./bin/{{ npm_name }} --bogus
if [ "$STATUS" -eq 2 ]; then ok "an unknown flag exits 2"; else bad "an unknown flag exits 2"; fi

run ./bin/{{ npm_name }} no-such-file.json
if [ "$STATUS" -eq 1 ]; then ok "a missing file exits 1"; else bad "a missing file exits 1"; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

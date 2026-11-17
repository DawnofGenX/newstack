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

if ! command -v ghdl >/dev/null 2>&1; then
  echo "smoke: ghdl is missing (install ghdl)"
  exit 1
fi

echo "smoke: vhdl-sim"

run ./run.sh
if [ "$STATUS" -eq 0 ]; then ok "run.sh passes"; else bad "run.sh passes"; printf '%s\n' "$OUT" | tail -8; fi

if printf '%s\n' "$OUT" | grep -q "PASS: counter testbench complete"; then
  ok "pass message present"
else
  bad "pass message present"
fi

set +e
ghdl -r --std=08 counter_tb -ginject_fault=true --assert-level=error --stop-time=10us >/dev/null 2>&1
st=$?
set -e
if [ "$st" -ne 0 ]; then ok "fault injection fails as expected"; else bad "fault injection fails as expected"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
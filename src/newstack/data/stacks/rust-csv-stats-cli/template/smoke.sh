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

echo "smoke: rust-csv-stats-cli"

run cargo test
if [ "$STATUS" -eq 0 ]; then ok "cargo test pass"; else bad "cargo test pass"; printf '%s\n' "$OUT" | tail -12; fi

set +e
OUT=$(cargo run --quiet -- tests/fixtures/stats.csv 2>&1)
STATUS=$?
set -e
if [ "$STATUS" -eq 0 ]; then ok "cli runs"; else bad "cli runs"; printf '%s\n' "$OUT" | tail -12; fi

if printf '%s\n' "$OUT" | grep -F "value count=3" >/dev/null; then
  ok "value count correct"
else
  bad "value count correct"
  printf '%s\n' "$OUT" | tail -8
fi

if printf '%s\n' "$OUT" | grep -F "unique=2" >/dev/null; then
  ok "value unique correct"
else
  bad "value unique correct"
  printf '%s\n' "$OUT" | tail -8
fi

if printf '%s\n' "$OUT" | grep -F "score count=3" >/dev/null; then
  ok "score count correct"
else
  bad "score count correct"
  printf '%s\n' "$OUT" | tail -8
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
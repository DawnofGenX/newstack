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

for tool in node npm; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "smoke: $tool is missing (install $tool)"
    exit 1
  fi
done

echo "smoke: node-cron-scheduler"

run npm test
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; printf '%s\n' "$OUT" | tail -8; fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

set +e
OUT=$(node src/cli.js --duration 3000 --store "$work/jobs.json" 2>&1)
STATUS=$?
set -e
if [ "$STATUS" -eq 0 ]; then ok "scheduler run exits cleanly"; else bad "scheduler run exits cleanly"; printf '%s\n' "$OUT" | tail -8; fi

if printf '%s\n' "$OUT" | grep -Eq 'ticks=[2-9][0-9]*'; then
  ok "job ran at least twice"
else
  bad "job ran at least twice"
  printf '%s\n' "$OUT" | tail -8
fi

if [ -s "$work/jobs.json" ] && grep -q '"lastRun"' "$work/jobs.json"; then
  ok "store records last run"
else
  bad "store records last run"
fi

rm -rf "$work"
trap - EXIT

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
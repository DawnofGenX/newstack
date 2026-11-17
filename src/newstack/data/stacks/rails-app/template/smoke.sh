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

if ! command -v ruby >/dev/null 2>&1; then
  echo "smoke: ruby is missing (install ruby)"
  exit 1
fi
if ! command -v bundle >/dev/null 2>&1; then
  echo "smoke: bundle is missing (install bundler)"
  exit 1
fi

echo "smoke: rails-app"

run bundle install --quiet
if [ "$STATUS" -eq 0 ]; then ok "bundle install"; else bad "bundle install"; printf '%s\n' "$OUT" | tail -8; fi

run bin/rails test
if [ "$STATUS" -eq 0 ]; then ok "rails tests pass"; else bad "rails tests pass"; printf '%s\n' "$OUT" | tail -8; fi

run bin/rails runner 'exit(TextStat.count("alpha beta\ngamma\n") == { lines: 2, words: 3, bytes: 17 } ? 0 : 1)'
if [ "$STATUS" -eq 0 ]; then ok "counts runner"; else bad "counts runner"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
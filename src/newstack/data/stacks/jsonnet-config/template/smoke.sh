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

if ! command -v jsonnet >/dev/null 2>&1; then
  echo "smoke: jsonnet is missing (install jsonnet)"
  exit 1
fi
if ! command -v make >/dev/null 2>&1; then
  echo "smoke: make is missing (install make)"
  exit 1
fi

echo "smoke: jsonnet-config"

run make build
if [ "$STATUS" -eq 0 ]; then ok "make build passes"; else bad "make build passes"; fi

run ./bin/{{ npm_name }} check
if [ "$STATUS" -eq 0 ]; then ok "check reports ok"; else bad "check reports ok"; printf '%s\n' "$OUT"; fi
# assert exact
if [ "$(./bin/{{ npm_name }} check)" = "ok" ]; then ok "check prints ok"; else bad "check prints ok"; fi

run ./bin/{{ npm_name }} test
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }
run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }

echo "smoke: {{ npm_name }}"

run mvn -B test
if [ "$STATUS" -eq 0 ]; then ok "tests"; else bad "tests"; printf '%s\n' "$OUT" | tail -8; fi

run mvn -B package -DskipTests
if [ "$STATUS" -eq 0 ]; then ok "package"; else bad "package"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

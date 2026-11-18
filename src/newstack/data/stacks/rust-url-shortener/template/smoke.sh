#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }
run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }

echo "smoke: {{ npm_name }}"

run cargo test
if [ "$STATUS" -eq 0 ]; then ok "tests"; else bad "tests"; printf '%s\n' "$OUT" | tail -8; fi

run cargo build --release
if [ "$STATUS" -eq 0 ]; then ok "build"; else bad "build"; printf '%s\n' "$OUT" | tail -8; fi

./target/release/{{ npm_name }} 5591 &
server=$!
sleep 1
run curl -sS -X POST http://127.0.0.1:5591/ -d 'https://example.com/x'
if [ "$STATUS" -eq 0 ]; then ok "create"; else bad "create"; printf '%s\n' "$OUT" | tail -8; fi
ID=$(printf '%s' "$OUT" | tr -d '\n')
run curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:5591/$ID
if [ "$STATUS" -eq 0 ]; then ok "redirect"; else bad "redirect"; printf '%s\n' "$OUT" | tail -8; fi
kill $server 2>/dev/null || true
wait $server 2>/dev/null || true

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

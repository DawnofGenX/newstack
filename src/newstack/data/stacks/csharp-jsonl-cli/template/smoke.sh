#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }
run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }

echo "smoke: {{ npm_name }}"

run dotnet test --nologo
if [ "$STATUS" -eq 0 ]; then ok "tests"; else bad "tests"; printf '%s\n' "$OUT" | tail -20; fi

printf '{"level":"info","n":1}\n{"level":"error","n":2}\n{"level":"info","n":3}\n' > /tmp/smoke.jsonl
run dotnet run -- /tmp/smoke.jsonl --where level=info
if [ "$STATUS" -eq 0 ]; then ok "filter"; else bad "filter"; printf '%s\n' "$OUT" | tail -20; fi

run dotnet run -- /tmp/smoke.jsonl --group level --count
if [ "$STATUS" -eq 0 ]; then ok "count"; else bad "count"; printf '%s\n' "$OUT" | tail -20; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

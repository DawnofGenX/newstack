#!/bin/sh
set -eu

PORT="${PORT:-5531}"
BASE="http://127.0.0.1:${PORT}"

echo "smoke: node-openapi-mock-server"

run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }

run npm test
if [ "$STATUS" -eq 0 ]; then echo "  ok   tests pass"; else echo "  FAIL tests pass"; printf '%s\n' "$OUT" | tail -10; exit 1; fi

work=$(mktemp -d)
trap 'if [ -n "${srv:-}" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

PORT="$PORT" node src/main.js >"$work/server.log" 2>&1 &
srv=$!
ready=0
i=0
while [ "$i" -lt 60 ]; do
  if curl --max-time 2 -s "$BASE/health" >/dev/null 2>&1; then ready=1; break; fi
  i=$((i + 1)); sleep 0.25
done
if [ "$ready" -ne 1 ]; then echo "  FAIL server ready"; cat "$work/server.log"; exit 1; fi
echo "  ok   server ready"

node tools/contract.mjs --base "$BASE" >"$work/contract.log" 2>&1
rc=$?
if [ "$rc" -ne 0 ]; then echo "  FAIL live contract"; cat "$work/contract.log"; exit 1; fi
cat "$work/contract.log"
echo "  ok   live contract"

kill "$srv" 2>/dev/null || true
wait "$srv" 2>/dev/null || true
srv=""
echo "smoke: PASS"
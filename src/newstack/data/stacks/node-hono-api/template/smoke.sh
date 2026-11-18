#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-hono-api"

npm test

PORT=18150 node src/server.js >/tmp/hono-smoke.log 2>&1 &
srv=$!
trap 'kill $srv 2>/dev/null || true; wait $srv 2>/dev/null || true' EXIT

ready=0
for _ in $(seq 1 60); do
  if curl --max-time 2 -sS http://127.0.0.1:18150/health >/dev/null 2>&1; then ready=1; break; fi
  if ! kill -0 "$srv" 2>/dev/null; then break; fi
  sleep 0.5
done
if [ "$ready" -ne 1 ]; then
  cat /tmp/hono-smoke.log >&2 || true
  echo "server did not become ready" >&2
  exit 1
fi

body=$(curl --max-time 10 -sS -X POST http://127.0.0.1:18150/items -H 'content-type: application/json' -d '{"name":"apple","price":1.5}')
echo "$body" | grep -q '"name":"apple"'
curl --max-time 10 -sS http://127.0.0.1:18150/items | grep -q '"apple"'
code=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18150/items/999)
test "$code" = "404"

kill $srv 2>/dev/null || true
wait $srv 2>/dev/null || true
trap - EXIT
echo "smoke: ok"
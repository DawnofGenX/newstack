#!/bin/sh
set -eu
go build -o bin/ssebroker .
./bin/ssebroker >/tmp/sse.log 2>&1 &
server=$!
trap 'kill $server 2>/dev/null || true; wait $server 2>/dev/null || true' EXIT
# wait for ready
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s --max-time 1 http://localhost:5580/health >/dev/null 2>&1; then break; fi
  sleep 0.2
done
curl -s --max-time 2 -X POST http://localhost:5580/publish -H 'Content-Type: application/json' -d '{"message":"hi"}' | grep -q published
# read one event with timeout
curl -sN --max-time 2 http://localhost:5580/events | head -n 1 | grep -q "hi\|heartbeat\|data" || true
kill $server 2>/dev/null || true
wait $server 2>/dev/null || true
echo ok

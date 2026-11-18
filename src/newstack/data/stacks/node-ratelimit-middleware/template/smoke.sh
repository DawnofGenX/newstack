#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-ratelimit-middleware"

npm test

PORT=5591 node src/server.js >/tmp/rl.log 2>&1 &
server=$!
trap 'kill $server 2>/dev/null || true; wait $server 2>/dev/null || true' EXIT

for i in $(seq 1 20); do
  if curl -s http://127.0.0.1:5591/stats >/dev/null 2>&1; then break; fi
  sleep 0.2
done

curl -s http://127.0.0.1:5591/stats | grep -q '"limit"'

# exhaust 10 (default) with limit override? use default 10
code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5591/)
echo "first: $code"
test "$code" = "200"

# hit many times to trigger 429
got429=0
for i in $(seq 1 20); do
  c=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5591/)
  if [ "$c" = "429" ]; then got429=1; break; fi
done
test "$got429" = "1"

echo "smoke: ok"

#!/bin/sh
set -eu
PORT=18081 node src/cli.js serve >/tmp/ff.log 2>&1 &
server=$!
trap 'kill $server 2>/dev/null || true' EXIT
for i in 1 2 3 4 5; do
  if curl -s http://localhost:18081/health >/dev/null 2>&1; then break; fi
  sleep 0.2
done
curl -s http://localhost:18081/flags?user=alice | grep -q '"flags"'
kill $server 2>/dev/null || true
wait $server 2>/dev/null || true
echo ok

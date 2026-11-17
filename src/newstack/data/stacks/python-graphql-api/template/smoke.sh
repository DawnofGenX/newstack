#!/bin/sh
set -eu

for tool in python curl; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "smoke: $tool is missing"
    exit 1
  fi
done

echo "smoke: python-graphql-api"

PORT=5530
BASE="http://127.0.0.1:${PORT}"

if curl -s --max-time 2 "$BASE/health" >/dev/null 2>&1; then
  echo "port $PORT is already answering - stop that process before running this step"
  exit 1
fi

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# run tests
if ! .venv/bin/python -m pytest >"$work/tests.log" 2>&1; then
  cat "$work/tests.log"
  exit 1
fi
echo "  ok   tests pass"

.venv/bin/python -m {{ package_name }} >"$work/server.log" 2>&1 &
srv=$!
ready=0
i=0
while [ "$i" -lt 60 ]; do
  if curl --max-time 2 -s "$BASE/health" >/dev/null 2>&1; then ready=1; break; fi
  i=$((i + 1))
  sleep 0.5
done
if [ "$ready" -ne 1 ]; then
  cat "$work/server.log"
  kill "$srv" 2>/dev/null || true
  wait "$srv" 2>/dev/null || true
  exit 1
fi

health=$(curl --max-time 10 -s "$BASE/health" || true)
echo "$health" | grep -q '"status": "ok"' || { echo "health failed: $health"; kill "$srv"; wait "$srv"; exit 1; }
echo "  ok   health"

resp=$(curl --max-time 10 -s -X POST "$BASE/graphql" -H 'content-type: application/json' -d '{"query":"{ hello add(a: 2, b: 3) }"}' || true)
echo "$resp" | grep -q '"hello": "world"' || { echo "query failed: $resp"; kill "$srv"; wait "$srv"; exit 1; }
echo "$resp" | grep -q '"add": 5' || { echo "query failed: $resp"; kill "$srv"; wait "$srv"; exit 1; }
echo "  ok   query result"

errresp=$(curl --max-time 10 -s -X POST "$BASE/graphql" -H 'content-type: application/json' -d '{"query":"{ user(id: 0) { id name } }"}' || true)
echo "$errresp" | grep -q '"path": \["user"\]' || { echo "error failed: $errresp"; kill "$srv"; wait "$srv"; exit 1; }
echo "  ok   error response"

kill "$srv" 2>/dev/null || true
wait "$srv" 2>/dev/null || true
echo "smoke: PASS"
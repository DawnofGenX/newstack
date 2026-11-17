#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
PORT=${PORT:-5511}
BASE="http://127.0.0.1:${PORT}"
LOG="$ROOT/.trpc-http.log"

if curl -fsS --max-time 2 "${BASE}/health" >/dev/null 2>&1; then
  echo "port ${PORT} is already answering - stop that process before running this step" >&2
  exit 1
fi

[ -d "$ROOT/dist" ] || (cd "$ROOT" && npm run -s build)

PORT=$PORT node "$ROOT/dist/src/main.js" >"$LOG" 2>&1 &
server=$!
trap 'kill -TERM $server 2>/dev/null || true; wait $server 2>/dev/null || true' EXIT

for _ in $(seq 1 160); do
  kill -0 "$server" 2>/dev/null || { cat "$LOG" >&2; echo "FAIL server exited before it answered" >&2; exit 1; }
  curl -fsS --max-time 2 "${BASE}/health" >/dev/null 2>&1 && break
  sleep 0.25
done
curl -fsS --max-time 2 "${BASE}/health" >/dev/null || { cat "$LOG" >&2; echo "FAIL server never answered" >&2; exit 1; }

health=$(curl -sS --max-time 2 "${BASE}/health")
echo "$health" | grep -q '"status":"ok"' || { echo "FAIL health body: $health" >&2; exit 1; }
echo "ok health"

hello=$(curl -sS --max-time 2 "${BASE}/hello?input=%7B%22name%22%3A%22world%22%7D")
echo "$hello" | grep -q '"Hello world"' || { echo "FAIL hello body: $hello" >&2; exit 1; }
echo "ok hello"

echo "smoke: all checks passed"
#!/usr/bin/env bash
# Live contract check: starts the built service, asserts every route, stops it.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
PORT=${PORT:-5460}
BASE="http://127.0.0.1:${PORT}"
LOG="$ROOT/.fastify-http.log"

if curl -fsS --max-time 2 "${BASE}/health" >/dev/null 2>&1; then
  echo "port ${PORT} is already answering - stop that process before running this step" >&2
  exit 1
fi

fail() { echo "FAIL $1" >&2; exit 1; }
check() { local name=$1 expected=$2 actual=$3; [ "$actual" = "$expected" ] || fail "$name: want [$expected] got [$actual]"; echo "ok $name"; }

[ -d "$ROOT/dist" ] || (cd "$ROOT" && npm run -s build)

PORT=$PORT node "$ROOT/dist/src/main.js" >"$LOG" 2>&1 &
server=$!
trap 'kill -TERM -"$server" 2>/dev/null || kill -TERM "$server" 2>/dev/null || true; wait "$server" 2>/dev/null || true' EXIT

for _ in $(seq 1 160); do
  kill -0 "$server" 2>/dev/null || { cat "$LOG" >&2; fail "server exited before it answered"; }
  curl -fsS --max-time 2 "${BASE}/health" >/dev/null 2>&1 && break
  sleep 0.25
done
curl -fsS --max-time 2 "${BASE}/health" >/dev/null || { cat "$LOG" >&2; fail "server never answered"; }

check health '{"status":"ok"}' "$(curl -sS --max-time 2 "${BASE}/health")"
check get '{"text":"a b","lines":0,"words":2,"bytes":3}' "$(curl -sS --max-time 2 "${BASE}/stats?text=a+b")"
check get-utf8 '{"text":"héllo wörld\n","lines":1,"words":2,"bytes":14}' "$(curl -sS --max-time 2 "${BASE}/stats?text=h%C3%A9llo+w%C3%B6rld%0A")"
check post '{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}' \
  "$(curl -sS --max-time 2 -X POST -H 'content-type: application/json' -d '{"text":"a b\nc\n"}' "${BASE}/stats")"
check missing '{"error":"missing_text"}' "$(curl -sS --max-time 2 -X POST -H 'content-type: application/json' -d '{}' "${BASE}/stats")"
check broken '{"error":"invalid_json"}' "$(curl -sS --max-time 2 -X POST -H 'content-type: application/json' -d '{"text":' "${BASE}/stats")"
check empty '{"text":"","lines":0,"words":0,"bytes":0}' "$(curl -sS --max-time 2 "${BASE}/stats?text=")"
check gone '{"error":"not_found","detail":"no route for GET /nope"}' "$(curl -sS --max-time 2 "${BASE}/nope")"
check wrong "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 2 -X DELETE "${BASE}/health")" "405"

echo "smoke: all checks passed"

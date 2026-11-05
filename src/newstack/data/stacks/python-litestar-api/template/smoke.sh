#!/usr/bin/env bash
# The contract through a real socket: start the service, assert every route with
# curl, stop it. Run after `uv venv && uv pip install -e .`.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
PORT=${PORT:-5464}
BASE="http://127.0.0.1:$PORT"
LOG=$(mktemp)

if curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1; then
  echo "port $PORT is already answering - stop that process before running this script" >&2
  rm -f "$LOG"
  exit 1
fi

PORT=$PORT "$ROOT/.venv/bin/python" -m {{ package_name }} >"$LOG" 2>&1 &
server=$!
trap 'kill -TERM $server 2>/dev/null || true; for _ in $(seq 1 20); do kill -0 $server 2>/dev/null || break; sleep 0.1; done; kill -KILL $server 2>/dev/null || true; wait $server 2>/dev/null || true; rm -f "$LOG"' EXIT

for _ in $(seq 1 200); do
  if curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1; then break; fi
  kill -0 $server 2>/dev/null || { echo "FAIL server exited before answering" >&2; cat "$LOG" >&2; exit 1; }
  sleep 0.25
done
curl -fsS --max-time 2 "$BASE/health" >/dev/null || { echo "FAIL server never answered on $PORT" >&2; cat "$LOG" >&2; exit 1; }

# code_and_body LABEL WANT_STATUS WANT_SUBSTRING -- curl args...
code_and_body() {
  local label=$1 want_status=$2 want_body=$3
  shift 3
  local out status body
  out=$(curl -sS --max-time 5 -w '\n%{http_code}' "$@")
  status=${out##*$'\n'}
  body=${out%$'\n'*}
  if [ "$status" != "$want_status" ]; then
    echo "FAIL $label: want status $want_status, got $status ($body)"; exit 1
  fi
  case "$body" in
    *"$want_body"*) echo "ok $label" ;;
    *) echo "FAIL $label: want *$want_body* in: $body"; exit 1 ;;
  esac
}

code_and_body health 200 '"status":"ok"' "$BASE/health"
code_and_body stats_get 200 '{"text":"a b","lines":1,"words":2,"bytes":3}' "$BASE/stats?text=a+b"
code_and_body stats_utf8 200 '"bytes":14' "$BASE/stats?text=h%C3%A9llo%20w%C3%B6rld%0A"
code_and_body stats_post 200 '"bytes":4' -X POST -H 'content-type: application/json' -d '{"text":"a b\n"}' "$BASE/stats"
code_and_body empty_text 200 '{"text":"","lines":0,"words":0,"bytes":0}' "$BASE/stats?text="
code_and_body missing_text 422 '{"error":"missing_text"}' "$BASE/stats"
code_and_body bad_escape 422 '{"error":"missing_text"}' "$BASE/stats?text=%zz"
code_and_body bad_json 422 '{"error":"invalid_json"}' -X POST -H 'content-type: application/json' -d 'not json' "$BASE/stats"
code_and_body wrong_member 422 '{"error":"missing_text"}' -X POST -H 'content-type: application/json' -d '{"text":1}' "$BASE/stats"
code_and_body wrong_method 405 '{"error":"method_not_allowed"}' -X PUT "$BASE/health"
code_and_body not_found 404 '"detail":"no route for GET /nope?x=1"' "$BASE/nope?x=1"
code_and_body head_is_405 405 '' -I "$BASE/health" -o /dev/null

echo "smoke: all checks passed"

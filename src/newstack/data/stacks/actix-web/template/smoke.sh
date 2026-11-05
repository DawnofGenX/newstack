#!/usr/bin/env bash
# Live smoke test for {{ npm_name }} on 127.0.0.1:5462.
set -e
set -o pipefail

BASE="http://127.0.0.1:5462"
DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$DIR/target/release/{{ npm_name }}"
[ -x "$BIN" ] || (cd "$DIR" && cargo build --release >/dev/null)

# --- pre-flight: refuse to stomp on a service already answering the port ---
if curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1; then
  echo "port 5462 is already answering - stop that process before running this step" >&2
  exit 1
fi

"$BIN" >/dev/null 2>&1 &
server=$!
cleanup() {
  kill -TERM "$server" 2>/dev/null || true
  wait "$server" 2>/dev/null || true
}
trap cleanup EXIT

# --- readiness poll: 160 x 0.25s, abort if the process died ---
ready=0
for _ in $(seq 1 160); do
  kill -0 "$server" 2>/dev/null || { echo "server died before bind" >&2; exit 1; }
  if curl -fsS --max-time 1 "$BASE/health" >/dev/null 2>&1; then ready=1; break; fi
  sleep 0.25
done
[ "$ready" = 1 ] || { echo "server not ready in 40s" >&2; exit 1; }

fail=0
check() { # check <desc> <expected-substring> <actual>
  if printf '%s' "$3" | grep -Fq "$2"; then
    echo "ok: $1"
  else
    echo "FAIL: $1 - expected '$2', got '$3'" >&2
    fail=1
  fi
}

body() { curl -sS -o /dev/null -w '%{http_code}' "$@"; }

# GET /health
check "GET /health body" '{"status":"ok"}' "$(curl -sS --max-time 2 "$BASE/health")"
check "GET /health status" "200" "$(body --max-time 2 "$BASE/health")"

# GET /stats?text=... (percent-decode %C3%A9 -> e-acute, '+' -> space)
r="$(curl -sS --max-time 2 "$BASE/stats?text=a+b")"
check "GET /stats a+b echo" '"text":"a b"' "$r"
check "GET /stats a+b counts" '"lines":0,"words":2,"bytes":3}' "$r"
r="$(curl -sS --max-time 2 "$BASE/stats?text=h%C3%A9llo+w%C3%B6rld%0A")"
check "GET /stats utf8 echo" '"text":"héllo wörld' "$r"
check "GET /stats utf8 counts" '"lines":1,"words":2,"bytes":14}' "$r"

# POST /stats JSON
r="$(curl -sS --max-time 2 -X POST -H 'content-type: application/json' -d '{"text":"a b\nc\n"}' "$BASE/stats")"
check "POST /stats echo" '"text":"a b\nc\n"' "$r"
check "POST /stats counts" '"lines":2,"words":3,"bytes":6}' "$r"
check "POST /stats key order" '{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}' "$r"
check "POST /stats empty" '"text":"","lines":0,"words":0,"bytes":0}' \
  "$(curl -sS --max-time 2 -X POST -d '{"text":""}' "$BASE/stats")"

# 422 branches
check "POST missing text status" "422" "$(body --max-time 2 -X POST -d '{"other":1}' "$BASE/stats")"
check "POST missing text body" '{"error":"missing_text"}' \
  "$(curl -sS --max-time 2 -X POST -d '{"other":1}' "$BASE/stats")"
check "POST non-string text" '{"error":"invalid_json"}' \
  "$(curl -sS --max-time 2 -X POST -d '{"text":42}' "$BASE/stats")"
check "POST malformed json" '{"error":"invalid_json"}' \
  "$(curl -sS --max-time 2 -X POST -d '{oops' "$BASE/stats")"
check "GET /stats no query status" "422" "$(body --max-time 2 "$BASE/stats")"
check "GET /stats no query body" '{"error":"missing_text"}' "$(curl -sS --max-time 2 "$BASE/stats")"

# 405 branches (wrong method on known routes)
check "POST /health 405 body" '{"error":"method_not_allowed"}' \
  "$(curl -sS --max-time 2 -X POST "$BASE/health")"
check "POST /health 405 status" "405" "$(body --max-time 2 -X POST "$BASE/health")"
check "DELETE /stats 405 body" '{"error":"method_not_allowed"}' \
  "$(curl -sS --max-time 2 -X DELETE "$BASE/stats")"

# 404 unknown path (detail excludes the query string)
check "404 body" '{"error":"not_found","detail":"no route for GET /nope"}' \
  "$(curl -sS --max-time 2 "$BASE/nope")"
check "404 detail excludes query" 'no route for POST /deep/path"' \
  "$(curl -sS --max-time 2 -X POST -d '{}' "$BASE/deep/path?x=1")"
check "404 status" "404" "$(body --max-time 2 "$BASE/anything")"

[ "$fail" = 0 ] || exit 1
echo "smoke: all checks passed"

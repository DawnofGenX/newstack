#!/usr/bin/env bash
# Live smoke test: starts the shaded jar on 5472 and asserts the contract with curl.
set -euo pipefail

cd "$(dirname "$0")"
JAR="target/{{ npm_name }}.jar"
BASE="http://127.0.0.1:5472"
[[ -f "$JAR" ]] || { echo "smoke: $JAR missing — run 'make build' first" >&2; exit 1; }

if curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1; then
  echo "smoke: a server is already answering on $BASE — stop it first" >&2
  exit 1
fi

work="$(mktemp -d)"
server=""
cleanup() {
  if [ -n "$server" ]; then
    kill -TERM "$server" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "$server" 2>/dev/null || break
      sleep 0.1
    done
    kill -KILL "$server" 2>/dev/null || true
    wait "$server" 2>/dev/null || true
  fi
  rm -rf "$work"
}
trap cleanup EXIT

java -jar "$JAR" >"$work/server.log" 2>&1 &
server=$!

ready=0
for _ in $(seq 1 160); do
  kill -0 "$server" 2>/dev/null || { echo "smoke: server died during startup" >&2; cat $work/server.log >&2; exit 1; }
  if curl -fsS --max-time 2 "$BASE/health" 2>/dev/null | grep -Fq '{"status":"ok"}'; then ready=1; break; fi
  sleep 0.25
done
[[ $ready -eq 1 ]] || { echo "smoke: server not ready after 40s" >&2; exit 1; }

fails=0
assert() { # <label> <expected> <actual>
  if [[ "$3" == "$2" ]]; then
    printf 'ok   %s\n' "$1"
  else
    printf 'FAIL %s\n  want %s\n  got  %s\n' "$1" "$2" "$3"
    fails=$((fails + 1))
  fi
}

get()  { curl -sS --max-time 5 "$BASE$1"; }
post() { curl -sS --max-time 5 -X POST -H 'Content-Type: application/json' --data-raw "$2" "$BASE$1"; }
code() { curl -sS --max-time 5 -o /dev/null -w '%{http_code}' "$@"; }

body=$(get '/health');                       assert 'GET /health'            '{"status":"ok"}' "$body"
body=$(get '/stats?text=a+b%0A');            assert 'GET stats a b\n'        '{"text":"a b\n","lines":1,"words":2,"bytes":4}' "$body"
body=$(get '/stats?text=h%C3%A9llo+w%C3%B6rld%0A'); assert 'GET stats utf8' '{"text":"héllo wörld\n","lines":1,"words":2,"bytes":14}' "$body"
body=$(get '/stats?text=a+b%0Ac%0A');        assert 'GET stats 2 lines'      '{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}' "$body"
body=$(get '/stats?text=');                  assert 'GET stats empty'        '{"text":"","lines":0,"words":0,"bytes":0}' "$body"

status=$(code "$BASE/stats?x=1");            assert 'GET missing text 422'   '422' "$status"
body=$(curl -sS --max-time 5 "$BASE/stats?x=1"); assert 'GET missing body'   '{"error":"missing_text"}' "$body"

body=$(post '/stats' '{"text":"a b\n"}');    assert 'POST stats'             '{"text":"a b\n","lines":1,"words":2,"bytes":4}' "$body"
status=$(code -X POST -H 'Content-Type: application/json' --data-raw '{"other":1}' "$BASE/stats")
assert 'POST missing text 422' '422' "$status"
body=$(curl -sS --max-time 5 -X POST --data-raw '{"other":1}' "$BASE/stats"); assert 'POST missing body' '{"error":"missing_text"}' "$body"
status=$(code -X POST --data-raw '{"text":42}' "$BASE/stats"); assert 'POST non-string 422' '422' "$status"
body=$(curl -sS --max-time 5 -X POST --data-raw '{"text":42}' "$BASE/stats"); assert 'POST invalid_json body' '{"error":"invalid_json"}' "$body"

status=$(code -X POST "$BASE/health");       assert 'POST /health 405'       '405' "$status"
status=$(code -X PUT "$BASE/stats");         assert 'PUT /stats 405'         '405' "$status"
status=$(code "$BASE/nope");                 assert 'GET /nope 404'          '404' "$status"
body=$(curl -sS --max-time 5 "$BASE/nope?text=x"); assert '404 body'          '{"error":"not_found","detail":"no route for GET /nope"}' "$body"

[[ $fails -eq 0 ]] || { echo "smoke: $fails assertion(s) failed" >&2; exit 1; }
echo "smoke: all checks passed"

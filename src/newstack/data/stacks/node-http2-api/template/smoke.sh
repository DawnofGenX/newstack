#!/usr/bin/env bash
# Talk to the service over HTTP/2 with prior knowledge, the way the README says to.
set -euo pipefail
cd "$(dirname "$0")"

PORT=${PORT:-5478}
BASE="http://127.0.0.1:$PORT"
LOG=".node-http2.log"

curl -fsS --max-time 2 --http2-prior-knowledge "$BASE/health" >/dev/null 2>&1 && {
  echo "port $PORT is already answering - stop that process before running this step" >&2
  exit 1
}

node src/main.js >"$LOG" 2>&1 &
server=$!
trap 'kill -TERM "$server" 2>/dev/null || true; wait "$server" 2>/dev/null || true' EXIT

for _ in $(seq 1 160); do
  if curl -fsS --max-time 2 --http2-prior-knowledge "$BASE/health" >/dev/null 2>&1; then break; fi
  sleep 0.25
done
kill -0 "$server" 2>/dev/null || { echo "the server died:" >&2; cat "$LOG" >&2; exit 1; }

call() { # method path [body] -> body
  if [ -n "${3:-}" ]; then
    curl -sS --max-time 10 --http2-prior-knowledge -X "$1" -d "$3" "$BASE$2"
  else
    curl -sS --max-time 10 --http2-prior-knowledge -X "$1" "$BASE$2"
  fi
}

status() { # method path [body] -> http status
  if [ -n "${3:-}" ]; then
    curl -sS --max-time 10 --http2-prior-knowledge -o /dev/null -w '%{http_code}' -X "$1" -d "$3" "$BASE$2"
  else
    curl -sS --max-time 10 --http2-prior-knowledge -o /dev/null -w '%{http_code}' -X "$1" "$BASE$2"
  fi
}

has() { # label haystack needle
  case "$2" in
    *"$3"*) echo "ok  $1" ;;
    *) echo "FAIL $1: expected '$3' in '$2'" >&2; exit 1 ;;
  esac
}

version=$(curl -sS --max-time 10 --http2-prior-knowledge -o /dev/null -w '%{http_version}' "$BASE/health")
if [ "$version" != "2" ]; then
  echo "FAIL the server did not answer over http/2 (got $version)" >&2
  exit 1
fi
echo "ok  http/2 negotiated"

has health "$(call GET /health)" '"status":"ok"'
has protocol "$(call GET /health)" '"protocol":"h2"'
has get "$(call GET '/stats?text=a%20b%0A')" '"lines":1,"words":2,"bytes":4'
has utf8 "$(call GET '/stats?text=h%C3%A9llo%20w%C3%B6rld%0A')" '"bytes":14'
has post "$(curl -sS --max-time 10 --http2-prior-knowledge -X POST -H 'content-type: application/json' -d '{"text":"a b\nc\n"}' "$BASE/stats")" '"lines":2,"words":3,"bytes":6'
has empty "$(call GET '/stats?text=')" '"lines":0,"words":0,"bytes":0'
has missing_text "$(call GET /stats)" '"error":"missing_text"'
has non_string "$(curl -sS --max-time 10 --http2-prior-knowledge -X POST -d '{"text":42}' "$BASE/stats")" '"error":"invalid_json"'
has broken_json "$(call POST /stats '{')" '"error":"invalid_json"'
has gone "$(call GET /nope)" '"detail":"no route for GET /nope"'
has wrong_method "$(call PUT /health)" '"error":"method_not_allowed"'

[ "$(status GET /nope)" = "404" ] && echo "ok  unknown route status" || { echo "FAIL unknown route status" >&2; exit 1; }
[ "$(status PUT /health)" = "405" ] && echo "ok  wrong method status" || { echo "FAIL wrong method status" >&2; exit 1; }
[ "$(status GET /stats)" = "422" ] && echo "ok  missing text status" || { echo "FAIL missing text status" >&2; exit 1; }

echo "smoke: all checks passed"

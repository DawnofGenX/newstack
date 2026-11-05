#!/usr/bin/env bash
# smoke.sh — live HTTP assertions against the notes API on :5471.
# Rules honored: no `curl -f` against expected 4xx (their bodies are the
# assertions); every curl carries a timeout; the EXIT trap releases the port.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-5471}"
BASE="http://127.0.0.1:${PORT}"
TMP="$(mktemp -d)"
DB="${TMP}/smoke.db"
BODY="${TMP}/body"
STATUS="${TMP}/status"
server=""
fail() { echo "smoke FAIL: $*" >&2; exit 1; }

# Pre-flight: refuse to hijack a port someone else is holding.
if curl -fsS --max-time 2 "${BASE}/health" >/dev/null 2>&1; then
  echo "smoke: a server is already listening on ${BASE} — stop it first" >&2
  exit 1
fi

trap 'kill -TERM "$server" 2>/dev/null || true
  for _ in $(seq 1 20); do kill -0 "$server" 2>/dev/null || break; sleep 0.1; done
  kill -KILL "$server" 2>/dev/null || true
  wait "$server" 2>/dev/null || true
  rm -rf "${TMP}"' EXIT

start_server() {
  DB_PATH="${DB}" PORT="${PORT}" bun run "${DIR}/src/main.js" >"${TMP}/server.log" 2>&1 &
  server=$!
  # Readiness: 160 x 0.25s, verifying each loop the child is still alive.
  local i
  for i in $(seq 1 160); do
    kill -0 "$server" 2>/dev/null || fail "server died during startup: $(cat "${TMP}/server.log")"
    curl -fsS --max-time 2 "${BASE}/health" >/dev/null 2>&1 && return 0
    sleep 0.25
  done
  fail "server not ready after 40s: $(cat "${TMP}/server.log")"
}

# chrome METHOD PATH DATA WANT_STATUS [NEEDLES...]  (DATA "" = no body)
chrome() {
  local method="$1" path="$2" data="$3" want="$4"; shift 4
  local out
  if [[ -n "$data" ]]; then
    out="$(curl -sS -m 5 -X "$method" -H 'content-type: application/json' -d "$data" -w '\n%{http_code}' "${BASE}${path}")"
  else
    out="$(curl -sS -m 5 -X "$method" -w '\n%{http_code}' "${BASE}${path}")"
  fi
  printf '%s' "${out%$'\n'*}" >"${BODY}"
  printf '%s' "${out##*$'\n'}" >"${STATUS}"
  [[ "$(cat "${STATUS}")" == "$want" ]] || fail "${method} ${path}: status $(cat "${STATUS}") want ${want} body $(cat "${BODY}")"
  local needle
  for needle in "$@"; do
    grep -Fq -- "$needle" "${BODY}" || fail "${method} ${path}: body $(cat "${BODY}") missing '${needle}'"
  done
  echo "ok: ${method} ${path} -> ${want}"
}

# jget FIELD — read one JSON field from the last response body
jget() { python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))[sys.argv[2]])' "${BODY}" "$1"; }

start_server

chrome GET    /health      ''    200 '{"status":"ok"' '"notes"'
chrome GET    /notes       ''    200 '"notes":[]'
chrome POST   /notes       '{"title":"shopping","body":"milk"}' 201 '"id":1' '"title":"shopping"' '"body":"milk"' '"created_at"'
grep -Fq '{"id":1,' "${BODY}" || fail "key order not id-first: $(cat "${BODY}")"
chrome POST   /notes       '{"title":"bare"}' 201 '"body":""'
chrome GET    /notes       ''    200 '"id":1' '"id":2'
chrome GET    /notes/1     ''    200 '"title":"shopping"'
chrome GET    /notes/99    ''    404 '{"error":"not_found"' 'no note with id 99'
chrome GET    /notes/abc   ''    404 '"detail":"no note with id abc"'
chrome PATCH  /notes/1     '{"title":"renamed"}' 200 '"title":"renamed"' '"body":"milk"'
chrome PATCH  /notes/1     '{"body":"eggs"}' 200 '"title":"renamed"' '"body":"eggs"' '"created_at"'
chrome PATCH  /notes/1     '{"title":"  "}' 422 'invalid_request' 'title: must not be blank'
chrome POST   /notes       '{"title":" "}' 422 '"error":"invalid_request"'
chrome POST   /notes       '{oops' 422 '{"error":"invalid_json"}'
chrome PUT    /notes       ''    405 '{"error":"method_not_allowed"}'
chrome PUT    /notes/1     ''    405 '{"error":"method_not_allowed"}'
chrome GET    /zzz?x=1     ''    404 'no route for GET /zzz'
chrome DELETE /notes/2     ''    204
chrome DELETE /notes/2     ''    404 'no note with id 2'
chrome DELETE /notes/999   ''    404
chrome GET    /health      ''    200 '"notes":1'

# Restart persistence: TERM the server, boot a new one on the same file.
kill -TERM "$server"; wait "$server" 2>/dev/null || true
start_server
chrome GET    /notes/1     ''    200 '"title":"renamed"' '"body":"eggs"'
chrome GET    /notes       ''    200 '"id":1'
if grep -Fq '"id":3' "${BODY}"; then fail "phantom row after restart: $(cat "${BODY}")"; fi
echo "ok: restart persistence (row 1 intact, no phantom rows)"

echo "smoke: all checks passed"

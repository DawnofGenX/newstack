#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# --- pre-flight: is something already serving the contract port? -------------
if curl -fsS --max-time 2 http://127.0.0.1:5467/health >/dev/null 2>&1; then
  echo "port 5467 is already answering" >&2
  exit 1
fi

PORT=5467
BASE="http://127.0.0.1:${PORT}"
BODY="$(mktemp)"
LOG="$(mktemp)"
server=""

stop_server() {
  [ -n "$server" ] || return 0
  kill -TERM -"$server" 2>/dev/null || kill -TERM "$server" 2>/dev/null || true
  wait "$server" 2>/dev/null || true
  server=""
}
trap 'stop_server; rm -f "$BODY" "$LOG"' EXIT

fail() { echo "SMOKE FAIL: $1" >&2; exit 1; }

start_server() {
  setsid node dist/src/server.js >"$LOG" 2>&1 &
  server=$!
  local ready=""
  # readiness poll: 160 x 0.25s = 40s max
  for _ in $(seq 1 160); do
    if curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1; then ready=1; break; fi
    kill -0 "$server" 2>/dev/null || { echo "server died:"; cat "$LOG" >&2; exit 1; }
    sleep 0.25
  done
  [ -n "$ready" ] || { echo "server not ready in 40s" >&2; exit 1; }
}

npm run build >/dev/null
npx prisma migrate deploy --schema prisma/schema.prisma >/dev/null

start_server

# --- GET /health -> 200 {"status":"ok","notes":N} -----------------------------
code="$(curl -sS -o "$BODY" -w '%{http_code}' "$BASE/health")"
[ "$code" = "200" ] || fail "health expected 200, got $code"
grep -Fq '"status":"ok"' "$BODY" || fail "health body: $(cat "$BODY")"
before="$(sed -n 's/.*"notes":\([0-9]*\).*/\1/p' < "$BODY")"
[ -n "$before" ] || fail "health notes count: $(cat "$BODY")"

# --- POST /notes -> 201 {id,title,body} ---------------------------------------
code="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$BASE/notes" \
  -H 'content-type: application/json' -d '{"title":"smoke-note","body":"persist me"}')"
[ "$code" = "201" ] || fail "create expected 201, got $code"
grep -Fq '"title":"smoke-note"' "$BODY" || fail "create body: $(cat "$BODY")"
id="$(sed -n 's/.*"id":\([0-9]*\).*/\1/p' < "$BODY")"
[ -n "$id" ] || fail "no id in create response: $(cat "$BODY")"

# --- POST /notes without body -> body defaults to "" --------------------------
code="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$BASE/notes" \
  -H 'content-type: application/json' -d '{"title":"nb"}')"
[ "$code" = "201" ] || fail "body-default expected 201, got $code"
grep -Fq '"body":""' "$BODY" || fail "body default: $(cat "$BODY")"
nb_id="$(sed -n 's/.*"id":\([0-9]*\).*/\1/p' < "$BODY")"

# --- blank / missing title -> 422 invalid_title --------------------------------
code="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$BASE/notes" \
  -H 'content-type: application/json' -d '{"title":"  ","body":"x"}')"
[ "$code" = "422" ] || fail "blank title expected 422, got $code"
grep -Fq '"error":"invalid_title"' "$BODY" || fail "blank title body: $(cat "$BODY")"
code="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$BASE/notes" \
  -H 'content-type: application/json' -d '{"body":"x"}')"
[ "$code" = "422" ] || fail "missing title expected 422, got $code"
grep -Fq '"error":"invalid_title"' "$BODY" || fail "missing title body: $(cat "$BODY")"

# --- GET /notes -> 200 array ordered by id asc ---------------------------------
code="$(curl -sS -o "$BODY" -w '%{http_code}' "$BASE/notes")"
[ "$code" = "200" ] || fail "list expected 200, got $code"
grep -o '"id":[0-9]*' < "$BODY" | cut -d: -f2 | \
  awk 'NR>1 && $1<=prev {bad=1} {prev=$1} END {exit bad?1:0}' \
  || fail "notes not ordered by id asc: $(cat "$BODY")"

# --- GET /notes/:id -> 200 ------------------------------------------------------
code="$(curl -sS -o "$BODY" -w '%{http_code}' "$BASE/notes/$id")"
[ "$code" = "200" ] || fail "get by id expected 200, got $code"
grep -Fq "\"id\":${id}" "$BODY" || fail "get by id body: $(cat "$BODY")"

# --- GET /notes/:id missing -> 404 exact shape ----------------------------------
code="$(curl -sS -o "$BODY" -w '%{http_code}' "$BASE/notes/99999999")"
[ "$code" = "404" ] || fail "missing note expected 404, got $code"
grep -Fq '"detail":"no note with id 99999999"' "$BODY" || fail "missing note body: $(cat "$BODY")"

# --- PATCH /notes/:id preserves untouched fields --------------------------------
code="$(curl -sS -o "$BODY" -w '%{http_code}' -X PATCH "$BASE/notes/$id" \
  -H 'content-type: application/json' -d '{"title":"renamed"}')"
[ "$code" = "200" ] || fail "patch expected 200, got $code"
grep -Fq '"title":"renamed"' "$BODY" || fail "patch title: $(cat "$BODY")"
grep -Fq '"body":"persist me"' "$BODY" || fail "patch dropped body: $(cat "$BODY")"

# --- DELETE /notes/:id -> 204, then GET -> 404 ----------------------------------
code="$(curl -sS -o "$BODY" -w '%{http_code}' -X DELETE "$BASE/notes/$nb_id")"
[ "$code" = "204" ] || fail "delete expected 204, got $code"
code="$(curl -sS -o "$BODY" -w '%{http_code}' "$BASE/notes/$nb_id")"
[ "$code" = "404" ] || fail "deleted note expected 404, got $code"

# --- wrong method -> 405 method_not_allowed --------------------------------------
for m in PUT PATCH DELETE; do
  code="$(curl -sS -o "$BODY" -w '%{http_code}' -X "$m" "$BASE/notes")"
  [ "$code" = "405" ] || fail "$m /notes expected 405, got $code"
  grep -Fq '"error":"method_not_allowed"' "$BODY" || fail "$m body: $(cat "$BODY")"
done
code="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$BASE/health")"
[ "$code" = "405" ] || fail "POST /health expected 405, got $code"
grep -Fq '"error":"method_not_allowed"' "$BODY" || fail "POST /health body: $(cat "$BODY")"

# --- malformed JSON -> 422 invalid_json -------------------------------------------
code="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST "$BASE/notes" \
  -H 'content-type: application/json' -d '{"title": "broken')"
[ "$code" = "422" ] || fail "invalid json expected 422, got $code"
grep -Fq '"error":"invalid_json"' "$BODY" || fail "invalid json body: $(cat "$BODY")"

# --- unknown path -> 404 not_found (path without query) -----------------------------
code="$(curl -sS -o "$BODY" -w '%{http_code}' "$BASE/zzz?x=1")"
[ "$code" = "404" ] || fail "unknown path expected 404, got $code"
grep -Fq '"detail":"no route for GET /zzz"' "$BODY" || fail "route 404 body: $(cat "$BODY")"

# --- restart persistence: kill, restart, row still there -----------------------------
stop_server
start_server
code="$(curl -sS -o "$BODY" -w '%{http_code}' "$BASE/notes/$id")"
[ "$code" = "200" ] || fail "after restart GET /notes/$id expected 200, got $code"
grep -Fq '"title":"renamed"' "$BODY" || fail "restart lost rename: $(cat "$BODY")"
grep -Fq '"body":"persist me"' "$BODY" || fail "restart lost body: $(cat "$BODY")"
echo "restart persistence: note $id survived ($(cat "$BODY"))"

echo "smoke: all checks passed"

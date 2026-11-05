#!/usr/bin/env bash
# Live contract check for the webhook receiver. Independent of the Python code under test:
# the digest is computed with openssl, exactly as a provider's sender would.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

HOST=127.0.0.1
PORT="${PORT:-5473}"
BASE="http://$HOST:$PORT"
SECRET="s3cr3t-value"
WORK="$(mktemp -d)"
LOG="$WORK/webhook.log"

fail() {
  echo "FAIL: $*" >&2
  [ -f "$LOG" ] && tail -20 "$LOG" >&2
  exit 1
}

if curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1; then
  fail "port $PORT is already answering - stop that process before running this step"
fi

cleanup() {
  if [ -n "${server:-}" ]; then
    kill -TERM "$server" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "$server" 2>/dev/null || break
      sleep 0.1
    done
    kill -KILL "$server" 2>/dev/null || true
    wait "$server" 2>/dev/null || true
  fi
  rm -rf "$WORK"
}
trap cleanup EXIT

DB_PATH="$WORK/events.db" WEBHOOK_SECRET_GITHUB="$SECRET" \
  .venv/bin/uvicorn {{ package_name }}.main:app --host "$HOST" --port "$PORT" >"$LOG" 2>&1 &
server=$!

ready=0
for _ in $(seq 1 160); do
  if curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1; then ready=1; break; fi
  sleep 0.25
done
[ "$ready" = "1" ] || fail "the server never answered on $BASE/health"
kill -0 "$server" 2>/dev/null || fail "the server exited before the first check"

digest() { # digest <timestamp> <body>
  printf '%s.%s' "$1" "$2" | openssl dgst -sha256 -hmac "$SECRET" -r | cut -d' ' -f1
}

call() { # call <method> <path> <body> <ts> <sig> <event-id>
  local method="$1" path="$2" body="$3" ts="$4" sig="$5" event="$6"
  curl -sS --max-time 5 -o "$WORK/body" -w '%{http_code}' -X "$method" "$BASE$path" \
    -H 'Content-Type: application/json' \
    -H "X-Timestamp: $ts" \
    -H "X-Signature: sha256=$sig" \
    -H "X-Event-Id: $event" \
    --data-binary "$body"
}

has() { # has <label> <needle>
  grep -Fq -- "$2" "$WORK/body" || fail "$1: expected $2 in $(cat "$WORK/body")"
}

TS="$(date +%s)"
BODY='{"kind": "push"}'
SIG="$(digest "$TS" "$BODY")"

status="$(curl -sS --max-time 5 -o "$WORK/body" -w '%{http_code}' "$BASE/health")"
[ "$status" = "200" ] || fail "health: expected 200, got $status"
has health '"events":0'

status="$(call POST /webhooks/github "$BODY" "$TS" "$SIG" evt-1)"
[ "$status" = "202" ] || fail "accept: expected 202, got $status ($(cat "$WORK/body"))"
has accept '"status":"accepted"'
has accept '"id":"evt-1"'
has accept '"kind":"push"'

status="$(call POST /webhooks/github "$BODY" "$TS" "$SIG" evt-1)"
[ "$status" = "200" ] || fail "duplicate: expected 200, got $status"
has duplicate '"status":"duplicate"'

status="$(curl -sS --max-time 5 -o "$WORK/body" -w '%{http_code}' "$BASE/health")"
has after-accept '"events":1'

status="$(call POST /webhooks/github "$BODY" "$TS" "$(digest "$TS" '{"kind": "other"}')" evt-2)"
[ "$status" = "401" ] || fail "bad signature: expected 401, got $status"
has bad-signature '"error":"bad_signature"'

OLD=$((TS - 3600))
status="$(call POST /webhooks/github "$BODY" "$OLD" "$(digest "$OLD" "$BODY")" evt-3)"
[ "$status" = "401" ] || fail "stale timestamp: expected 401, got $status"
has stale '"error":"stale_timestamp"'

status="$(curl -sS --max-time 5 -o "$WORK/body" -w '%{http_code}' -X POST "$BASE/webhooks/github" \
  -H 'Content-Type: application/json' \
  -H "X-Timestamp: $TS" -H "X-Signature: sha256=$SIG" --data-binary "$BODY")"
[ "$status" = "400" ] || fail "missing id header: expected 400, got $status"
has unsigned '"error":"missing_event_id"'

BROKEN='{"kind": '
status="$(call POST /webhooks/github "$BROKEN" "$TS" "$(digest "$TS" "$BROKEN")" evt-4)"
[ "$status" = "422" ] || fail "invalid json: expected 422, got $status"
has invalid-json '"error":"invalid_json"'

status="$(call POST /webhooks/gitlab "$BODY" "$TS" "$SIG" evt-5)"
[ "$status" = "404" ] || fail "unknown source: expected 404, got $status"
has unknown-source '"error":"unknown_source"'

status="$(curl -sS --max-time 5 -o "$WORK/body" -w '%{http_code}' "$BASE/events")"
[ "$status" = "200" ] || fail "events: expected 200, got $status"
has events '"id":"evt-1"'
has events '"source":"github"'

status="$(curl -sS --max-time 5 -o "$WORK/body" -w '%{http_code}' "$BASE/nope")"
[ "$status" = "404" ] || fail "unknown route: expected 404, got $status"
has not-found '"detail":"no route for GET /nope"'

status="$(curl -sS --max-time 5 -o "$WORK/body" -w '%{http_code}' -X PATCH "$BASE/health")"
[ "$status" = "405" ] || fail "wrong method: expected 405, got $status"
has method '"error":"method_not_allowed"'

[ -f "$WORK/events.db" ] || fail "the receiver never created its database file"

echo "smoke: all checks passed"

#!/usr/bin/env bash
# Contract check over a real socket. Every assertion greps a literal fragment.
set -euo pipefail

PORT="${PORT:-5470}"
BASE="http://127.0.0.1:$PORT"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
fail=0

cleanup() {
  rm -rf "$work"
  if [ -n "${server:-}" ]; then
    kill -TERM -"$server" 2>/dev/null || kill "$server" 2>/dev/null || true
    for _ in $(seq 1 20); do kill -0 "$server" 2>/dev/null || break; sleep 0.1; done
    kill -KILL "$server" 2>/dev/null || true
    wait "$server" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1; then
  echo "port $PORT is already answering - stop that process before running this step"
  exit 1
fi

cd "$ROOT"
cargo build --release >/dev/null 2>&1
DB_PATH="$work/notes.db" PORT="$PORT" ./target/release/{{ npm_name }} >"$work/server.log" 2>&1 &
server=$!
for _ in $(seq 1 160); do
  curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1 && break
  sleep 0.25
done
kill -0 "$server" 2>/dev/null || { echo "server died:"; cat "$work/server.log"; exit 1; }

check() {
  local name="$1" want="$2" hay="$3"
  if printf '%s' "$hay" | grep -Fq -- "$want"; then
    echo "ok   $name"
  else
    echo "FAIL $name: want [$want] in [$hay]"
    fail=1
  fi
}

body() { curl -sS --max-time 5 "$@"; }
code() { curl -sS --max-time 5 -o "$work/last.body" -w '%{http_code}' "$@"; }

check health '"status":"ok"' "$(body "$BASE/health")"
check health-notes '"notes":0' "$(body "$BASE/health")"

created="$(body -X POST "$BASE/notes" -H 'content-type: application/json' -d '{"title":"shopping","body":"milk"}')"
check create-id '"id":1' "$created"
check create-title '"title":"shopping"' "$created"
check create-body '"body":"milk"' "$created"
check create-stamp '"created_at":"' "$created"

check list-title '"title":"shopping"' "$(body "$BASE/notes")"
check list-wrapped '"notes":[' "$(body "$BASE/notes")"

check get-title '"title":"shopping"' "$(body "$BASE/notes/1")"

patched="$(body -X PATCH "$BASE/notes/1" -H 'content-type: application/json' -d '{"title":"groceries"}')"
check patch-title '"title":"groceries"' "$patched"
check patch-keeps-body '"body":"milk"' "$patched"

check blank-code 422 "$(code -X POST "$BASE/notes" -H 'content-type: application/json' -d '{"title":"   "}')"
check blank-detail '"detail":"title: must not be blank"' "$(cat "$work/last.body")"
check blank-no-create '"notes":1' "$(body "$BASE/health")"

check missing-code 422 "$(code -X POST "$BASE/notes" -H 'content-type: application/json' -d '{"body":"x"}')"
check missing-detail '"title: is required"' "$(cat "$work/last.body")"

check broken-code 422 "$(code -X POST "$BASE/notes" -H 'content-type: application/json' -d '{oops}')"
check broken-body '"error":"invalid_json"' "$(cat "$work/last.body")"
if grep -Fq '"detail"' "$work/last.body"; then echo "FAIL broken-no-detail"; fail=1; else echo "ok   broken-no-detail"; fi

check gone-code 404 "$(code "$BASE/notes/99")"
check gone-detail '"detail":"no note with id 99"' "$(cat "$work/last.body")"

check junk-id-code 404 "$(code "$BASE/notes/abc")"
check junk-id-detail 'no route for GET /notes/abc' "$(cat "$work/last.body")"

check nope-code 404 "$(code "$BASE/nope")"
check nope-detail '"detail":"no route for GET /nope"' "$(cat "$work/last.body")"

check wrong-code 405 "$(code -X PUT "$BASE/health")"
check wrong-body '"error":"method_not_allowed"' "$(cat "$work/last.body")"

check delete-code 204 "$(code -X DELETE "$BASE/notes/1")"
check delete-gone-code 404 "$(code "$BASE/notes/1")"
check delete-count '"notes":0' "$(body "$BASE/health")"

check db-file yes "$([ -s "$work/notes.db" ] && echo yes || echo no)"

[ "$fail" -eq 0 ] || { echo "smoke: FAILED"; exit 1; }
echo "smoke: all checks passed"

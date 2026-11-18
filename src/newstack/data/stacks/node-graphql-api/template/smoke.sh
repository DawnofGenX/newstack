#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

run() {
  set +e
  OUT=$("$@" 2>&1)
  STATUS=$?
  set -e
}

for tool in node npm curl; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "smoke: $tool is missing (install $tool)"
    exit 1
  fi
done

echo "smoke: node-graphql-api"

run npm test
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; printf '%s\n' "$OUT" | tail -8; fi

PORT=18091
BASE="http://127.0.0.1:${PORT}"
work=$(mktemp -d)
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

PORT="$PORT" node src/main.js >"$work/server.log" 2>&1 &
srv=$!
ready=0
i=0
while [ "$i" -lt 60 ]; do
  if curl --max-time 2 -sS "${BASE}/graphql" >/dev/null 2>&1; then ready=1; break; fi
  if ! kill -0 "$srv" 2>/dev/null; then break; fi
  i=$((i + 1))
  sleep 0.5
done
if [ "$ready" -eq 1 ]; then
  ok "server becomes ready"

  set +e
  resp=$(curl --max-time 10 -sS -X POST "${BASE}/graphql" -H 'content-type: application/json' -d '{"query":"mutation { addNote(title:\"smoke\", body:\"hello\") { id title body } }"}')
  rc=$?
  set -e
  if [ "$rc" -eq 0 ] && printf '%s' "$resp" | grep -q '"title":"smoke"'; then
    ok "mutation returns the note"
  else
    bad "mutation returns the note"
    printf '%s\n' "$resp" >&2
  fi

  set +e
  resp=$(curl --max-time 10 -sS -X POST "${BASE}/graphql" -H 'content-type: application/json' -d '{"query":"{ notes { id title } }"}')
  rc=$?
  set -e
  if [ "$rc" -eq 0 ] && printf '%s' "$resp" | grep -q '"title":"smoke"'; then
    ok "query lists the note"
  else
    bad "query lists the note"
    printf '%s\n' "$resp" >&2
  fi
else
  bad "server becomes ready"
  cat "$work/server.log" >&2 || true
fi

kill "$srv" 2>/dev/null || true
wait "$srv" 2>/dev/null || true
srv=""
trap - EXIT
rm -rf "$work"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
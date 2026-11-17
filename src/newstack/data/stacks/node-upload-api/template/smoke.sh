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

if ! command -v node >/dev/null 2>&1; then
  echo "smoke: node is missing (install node)"
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "smoke: npm is missing (install npm)"
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "smoke: curl is missing (install curl)"
  exit 1
fi

echo "smoke: node-upload-api"

run npm test
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; printf '%s\n' "$OUT" | tail -8; fi

PORT=18094
BASE="http://127.0.0.1:${PORT}"
work=$(mktemp -d)
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

UPLOAD_DIR="$work/data" PORT="$PORT" node src/main.js >"$work/server.log" 2>&1 &
srv=$!
ready=0
i=0
while [ "$i" -lt 60 ]; do
  if curl --max-time 2 -fsS "${BASE}/health" >/dev/null 2>&1; then ready=1; break; fi
  i=$((i + 1))
  sleep 0.5
done
if [ "$ready" -eq 1 ]; then
  ok "server becomes ready"
  code=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' "${BASE}/health")
  if [ "$code" = "200" ]; then ok "health status"; else bad "health status"; fi

  code=$(curl --max-time 10 -s -o "$work/create.json" -w '%{http_code}' -X POST -H 'content-type: application/json' -d '{"name":"smoke.txt","size":5}' "${BASE}/uploads")
  if [ "$code" = "201" ]; then ok "create upload returns 201"; else bad "create upload returns 201"; fi
  if grep -q '"id"' "$work/create.json" 2>/dev/null; then ok "upload has id"; else bad "upload has id"; fi
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
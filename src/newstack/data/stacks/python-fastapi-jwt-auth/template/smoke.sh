#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5520}"
HOST="127.0.0.1"

# fail fast if port already answering
if curl -sf "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then
  echo "port ${PORT} already in use" >&2
  exit 1
fi

JWT_SECRET=test-secret AUTH_USERS='{"alice":"wonderland"}' \
  .venv/bin/uvicorn {{ package_name }}.main:app --host "${HOST}" --port "${PORT}" >/tmp/jwt-smoke.log 2>&1 &
SRV=$!
cleanup() { kill "${SRV}" 2>/dev/null || true; wait "${SRV}" 2>/dev/null || true; }
trap cleanup EXIT

for i in $(seq 1 50); do
  if curl -sf "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then break; fi
  sleep 0.2
done
curl -sf "http://${HOST}:${PORT}/health" >/dev/null

TOKEN=$(curl -sf -X POST "http://${HOST}:${PORT}/token" -H 'Content-Type: application/json' -d '{"username":"alice","password":"wonderland"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
echo "token issued"

code=$(curl -s -o /tmp/me.json -w '%{http_code}' "http://${HOST}:${PORT}/me" -H "Authorization: Bearer ${TOKEN}")
test "${code}" = "200"

code2=$(curl -s -o /dev/null -w '%{http_code}' "http://${HOST}:${PORT}/me")
test "${code2}" = "401"

echo "smoke: PASS"
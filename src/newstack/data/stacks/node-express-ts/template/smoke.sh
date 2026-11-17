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

echo "smoke: node-express-ts"

run npm install --no-audit --no-fund
if [ "$STATUS" -eq 0 ]; then ok "npm install"; else bad "npm install"; fi

run npm run typecheck
if [ "$STATUS" -eq 0 ]; then ok "typecheck passes"; else bad "typecheck passes"; fi

run npm test
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; fi

PORT=54321
BASE="http://127.0.0.1:${PORT}"
PORT="$PORT" npm run start >.srv.log 2>&1 &
srv=$!
trap 'kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; rm -f .srv.log' EXIT
ready=0
i=0
while [ "$i" -lt 60 ]; do
  if curl --max-time 2 -fsS "${BASE}/health" >/dev/null 2>&1; then ready=1; break; fi
  i=$((i + 1))
  sleep 0.5
done
if [ "$ready" -eq 1 ]; then
  ok "server becomes ready"
  health=$(curl --max-time 10 -fsS "${BASE}/health" || true)
  if printf '%s' "$health" | grep -q '"status":"ok"'; then ok "health body"; else bad "health body"; fi

  code=$(curl --max-time 10 -s -o /tmp/item.json -w '%{http_code}' -X POST -H 'content-type: application/json' -d '{"name":"smoke"}' "${BASE}/items")
  if [ "$code" = "201" ]; then ok "POST /items returns 201"; else bad "POST /items returns 201"; fi
  if grep -q '"name":"smoke"' /tmp/item.json; then ok "created item echoed"; else bad "created item echoed"; fi
  rm -f /tmp/item.json
else
  bad "server becomes ready"
  cat .srv.log >&2 || true
fi
kill "$srv" 2>/dev/null || true
wait "$srv" 2>/dev/null || true
trap - EXIT
rm -f .srv.log

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
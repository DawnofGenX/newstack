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

echo "smoke: nest-api"

run npm install --no-audit --no-fund
if [ "$STATUS" -eq 0 ]; then ok "npm install"; else bad "npm install"; printf '%s\n' "$OUT" | tail -8; fi

run npm run typecheck
if [ "$STATUS" -eq 0 ]; then ok "typecheck passes"; else bad "typecheck passes"; printf '%s\n' "$OUT" | tail -8; fi

run npm test
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; printf '%s\n' "$OUT" | tail -8; fi

run npm run build
if [ "$STATUS" -eq 0 ]; then ok "build passes"; else bad "build passes"; printf '%s\n' "$OUT" | tail -8; fi

PORT=18093
BASE="http://127.0.0.1:${PORT}"
work=$(mktemp -d)
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

PORT="$PORT" node dist/main.js >"$work/server.log" 2>&1 &
srv=$!
ready=0
i=0
while [ "$i" -lt 60 ]; do
  if curl --max-time 2 -fsS "${BASE}/" >/dev/null 2>&1; then ready=1; break; fi
  i=$((i + 1))
  sleep 0.5
done
if [ "$ready" -eq 1 ]; then
  ok "server becomes ready"
  body=$(curl --max-time 10 -fsS "${BASE}/" || true)
  if printf '%s' "$body" | grep -q 'Hello from'; then ok "root greeting"; else bad "root greeting"; fi

  stats=$(curl --max-time 10 -fsS "${BASE}/stats?text=hello%20world%0A" || true)
  if printf '%s' "$stats" | grep -q '"lines":1'; then ok "stats body"; else bad "stats body"; fi
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
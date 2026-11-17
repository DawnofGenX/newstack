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

echo "smoke: openapi-spec"

run npm install --no-audit --no-fund
if [ "$STATUS" -eq 0 ]; then ok "npm install"; else bad "npm install"; fi

run npm run check
if [ "$STATUS" -eq 0 ]; then ok "check passes"; else bad "check passes"; printf '%s\n' "$OUT" | tail -12; fi

if [ -f dist/index.html ]; then ok "docs build artifact exists"; else bad "docs build artifact exists"; fi

# HTTP probe on an ephemeral-ish fixed port
PORT=5499
BASE="http://127.0.0.1:${PORT}"
if command -v curl >/dev/null 2>&1; then
  PORT="$PORT" node src/main.js >.oas.log 2>&1 &
  srv=$!
  trap 'kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; rm -f .oas.log' EXIT
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
  else
    bad "server becomes ready"
    cat .oas.log >&2 || true
  fi
  kill "$srv" 2>/dev/null || true
  wait "$srv" 2>/dev/null || true
  trap - EXIT
  rm -f .oas.log
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
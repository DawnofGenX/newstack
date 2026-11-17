#!/bin/sh
set -eu

echo "smoke: go-slog-middleware"

PORT="${PORT:-5532}"
BASE="http://127.0.0.1:${PORT}"

# fail fast if port already answering
if curl -sS --max-time 1 "$BASE/health" >/dev/null 2>&1; then
  echo "  FAIL port $PORT already in use"; exit 1
fi

go build -o bin/server .
LOG=$(mktemp)
PORT="$PORT" bin/server >"$LOG" 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null || true; wait $PID 2>/dev/null || true; rm -f "$LOG"' EXIT

# wait for readiness
i=0
while [ $i -lt 50 ]; do
  if curl -sS --max-time 1 "$BASE/health" >/dev/null 2>&1; then break; fi
  i=$((i+1)); sleep 0.2
done

code=$(curl -sS -o /tmp/slog-health.json -w '%{http_code}' "$BASE/health")
if [ "$code" != "200" ]; then echo "  FAIL health $code"; cat "$LOG"; exit 1; fi
echo "  ok   health 200"

code=$(curl -sS -o /tmp/slog-panic.json -w '%{http_code}' "$BASE/panic")
if [ "$code" != "500" ]; then echo "  FAIL panic $code"; cat "$LOG"; exit 1; fi
echo "  ok   panic 500"

# redaction: send Authorization header and ensure token not in logs
curl -sS -H 'Authorization: Bearer secret-token' "$BASE/health" >/dev/null
sleep 0.3
if grep -q 'secret-token' "$LOG"; then echo "  FAIL token leaked in logs"; cat "$LOG"; exit 1; fi
echo "  ok   authorization redacted"

# log lines structured
if ! grep -q '"method":"GET"' "$LOG" && ! grep -q '"method": "GET"' "$LOG"; then
  # slog JSON may have spaces? check looser
  if ! grep -q 'GET' "$LOG"; then echo "  FAIL no log lines"; cat "$LOG"; exit 1; fi
fi
echo "  ok   log lines present"

echo "smoke: PASS"
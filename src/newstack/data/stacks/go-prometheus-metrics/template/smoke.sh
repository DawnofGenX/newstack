#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }

echo "smoke: go-prometheus-metrics"

run go vet ./...
if [ "$STATUS" -eq 0 ]; then ok "go vet passes"; else bad "go vet passes"; printf '%s\n' "$OUT" | tail -8; fi

run go test ./...
if [ "$STATUS" -eq 0 ]; then ok "go test passes"; else bad "go test passes"; printf '%s\n' "$OUT" | tail -8; fi

run go build -o bin/server .
if [ "$STATUS" -eq 0 ]; then ok "go build"; else bad "go build"; printf '%s\n' "$OUT" | tail -8; fi

PORT=5543
BASE="http://127.0.0.1:${PORT}"
work=$(mktemp -d)
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

if [ -x ./bin/server ]; then
  PORT="$PORT" ./bin/server >"$work/server.log" 2>&1 &
  srv=$!
  ready=0
  i=0
  while [ "$i" -lt 60 ]; do
    code=$(curl --max-time 2 -sS -o /dev/null -w '%{http_code}' "${BASE}/health" 2>/dev/null || true)
    if [ "$code" = "200" ]; then ready=1; break; fi
    i=$((i + 1))
    sleep 0.5
  done
  if [ "$ready" -eq 1 ]; then
    ok "server becomes ready"
    metrics=$(curl --max-time 10 -sS "${BASE}/metrics" 2>/dev/null || true)
    if printf '%s' "$metrics" | grep -q 'http_requests_total'; then ok "counter metric present"; else bad "counter metric present"; fi
    if printf '%s' "$metrics" | grep -q 'http_request_duration_seconds'; then ok "histogram metric present"; else bad "histogram metric present"; fi
    if printf '%s' "$metrics" | grep -q 'http_requests_total [0-9]'; then ok "counter has numeric value"; else bad "counter has numeric value"; fi
  else
    bad "server becomes ready"
    cat "$work/server.log" >&2 || true
  fi
  kill "$srv" 2>/dev/null || true
  wait "$srv" 2>/dev/null || true
  srv=""
else
  bad "server binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

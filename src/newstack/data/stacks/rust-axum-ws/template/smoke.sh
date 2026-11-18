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

echo "smoke: rust-axum-ws"

run cargo test
if [ "$STATUS" -eq 0 ]; then ok "cargo test pass"; else bad "cargo test pass"; printf '%s\n' "$OUT" | tail -12; fi

# Build first so startup is fast.
run cargo build
if [ "$STATUS" -ne 0 ]; then bad "cargo build"; printf '%s\n' "$OUT" | tail -12; printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"; exit 1; fi

./target/debug/{{ npm_name }} >/tmp/axum-ws.log 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; rm -f /tmp/axum-ws.log' EXIT

READY=0
i=0
while [ "$i" -lt 50 ]; do
  set +e
  RESP=$(curl -sS http://127.0.0.1:5552/health 2>&1)
  STATUS=$?
  set -e
  if [ "$STATUS" -eq 0 ] && [ "$RESP" = "ok" ]; then
    READY=1
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "server exited early:"
    cat /tmp/axum-ws.log 2>/dev/null || true
    break
  fi
  i=$((i + 1))
  sleep 0.2
done

if [ "$READY" -eq 1 ]; then
  ok "health endpoint returns ok"
else
  bad "health endpoint returns ok"
fi

kill "$SERVER_PID" 2>/dev/null || true
wait "$SERVER_PID" 2>/dev/null || true
trap - EXIT
rm -f /tmp/axum-ws.log

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
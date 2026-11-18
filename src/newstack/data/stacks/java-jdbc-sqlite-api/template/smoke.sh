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

echo "smoke: java-jdbc-sqlite-api"

run mvn -q test
if [ "$STATUS" -eq 0 ]; then ok "mvn test pass"; else bad "mvn test pass"; printf '%s\n' "$OUT" | tail -20; fi

run mvn -q -o package -DskipTests
if [ "$STATUS" -ne 0 ]; then
  # fall back to online build if offline fails
  run mvn -q package -DskipTests
fi
if [ "$STATUS" -eq 0 ]; then ok "mvn package pass"; else bad "mvn package pass"; printf '%s\n' "$OUT" | tail -20; fi

JAR="target/{{ npm_name }}.jar"
if [ ! -f "$JAR" ]; then
  bad "jar exists"
  printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
  exit 1
fi
ok "jar exists"

java -jar "$JAR" >/tmp/java-api.log 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true; rm -f /tmp/java-api.log' EXIT

READY=0
i=0
while [ "$i" -lt 60 ]; do
  set +e
  RESP=$(curl -sS http://127.0.0.1:5553/health 2>&1)
  STATUS=$?
  set -e
  if [ "$STATUS" -eq 0 ] && [ "$RESP" = "ok" ]; then
    READY=1
    break
  fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "server exited early:"
    cat /tmp/java-api.log 2>/dev/null || true
    break
  fi
  i=$((i + 1))
  sleep 0.5
done

if [ "$READY" -eq 1 ]; then
  ok "health endpoint returns ok"
else
  bad "health endpoint returns ok"
fi

# POST a note
set +e
RESP=$(curl -sS -X POST http://127.0.0.1:5553/notes -H 'Content-Type: application/json' -d '{"title":"smoke","body":"hello"}' 2>&1)
STATUS=$?
set -e
if [ "$STATUS" -eq 0 ] && printf '%s' "$RESP" | grep -q 'smoke'; then
  ok "POST note succeeds"
else
  bad "POST note succeeds"
  printf '%s\n' "$RESP"
fi

# GET notes
set +e
RESP=$(curl -sS http://127.0.0.1:5553/notes 2>&1)
STATUS=$?
set -e
if [ "$STATUS" -eq 0 ] && printf '%s' "$RESP" | grep -q 'smoke'; then
  ok "GET notes lists note"
else
  bad "GET notes lists note"
  printf '%s\n' "$RESP"
fi

# DELETE note
set +e
RESP=$(curl -sS -X DELETE http://127.0.0.1:5553/notes/smoke 2>&1)
STATUS=$?
set -e
if [ "$STATUS" -eq 0 ]; then
  ok "DELETE note succeeds"
else
  bad "DELETE note succeeds"
  printf '%s\n' "$RESP"
fi

kill "$SERVER_PID" 2>/dev/null || true
wait "$SERVER_PID" 2>/dev/null || true
trap - EXIT
rm -f /tmp/java-api.log

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
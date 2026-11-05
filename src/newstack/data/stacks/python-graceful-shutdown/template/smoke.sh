#!/usr/bin/env bash
# End-to-end: real signals, real sockets, real exit codes.
#
#   PY=.venv/bin/python bash smoke.sh
set -euo pipefail

PY="${PY:-python}"
PORT="${PORT:-5477}"
cd "$(dirname "$0")"

failures=0
check() {
  local name="$1"
  local status="$2"
  if [ "$status" -eq 0 ]; then
    printf 'ok   %s\n' "$name"
  else
    printf 'FAIL %s\n' "$name"
    failures=$((failures + 1))
  fi
}

get() {
  "$PY" -c 'import sys, urllib.request
url = "http://127.0.0.1:" + sys.argv[1] + sys.argv[2]
with urllib.request.urlopen(url, timeout=20) as response:
    print(response.status, response.read().decode().strip())' "$1" "$2"
}

wait_for() {
  local file="$1" pattern="$2"
  for _ in $(seq 1 200); do
    if grep -q "$pattern" "$file" 2>/dev/null; then return 0; fi
    sleep 0.05
  done
  return 1
}

log=$(mktemp)
body=$(mktemp)
trap 'rm -f "$log" "$body"' EXIT

# --- a request in flight when the signal arrives -------------------------------
"$PY" -m {{ package_name }} serve --port "$PORT" --drain-timeout 5 >"$log" 2>&1 &
server=$!
wait_for "$log" "listening" ; check "the server listens" $?

health=$(get "$PORT" /health)
test "$health" = "200 ok" ; check "health answers before the drain" $?

get "$PORT" "/work?ms=700" >"$body" 2>&1 &
request=$!
sleep 0.3
kill -TERM "$server"

set +e
wait "$server"
status=$?
wait "$request"
request_status=$?
set -e

test "$status" -eq 0 ; check "SIGTERM mid-request exits 0" $?
test "$request_status" -eq 0 ; check "the in-flight request completed" $?
grep -q "done" "$body" ; check "and it got its body, not a reset" $?
grep -q "draining 1 request(s)" "$log" ; check "the drain counted the request" $?
grep -q "drained 1 request(s)" "$log" ; check "the drain waited for it" $?
grep -q "^stopped" "$log" ; check "the process said goodbye" $?

# --- a second signal does not wait for a hung request -------------------------
"$PY" -m {{ package_name }} serve --port "$((PORT + 1))" --drain-timeout 30 >"$log" 2>&1 &
server=$!
wait_for "$log" "listening"
get "$((PORT + 1))" "/work?ms=5000" >"$body" 2>&1 &
request=$!
sleep 0.3
kill -TERM "$server"
sleep 0.3
kill -TERM "$server"

set +e
wait "$server"
status=$?
wait "$request"
request_status=$?
set -e

test "$status" -eq 130 ; check "a second signal exits 130" $?
grep -q "forcing exit" "$log" ; check "and says why" $?
# Killing the client ourselves would print a job-control "Killed" line; letting it
# notice the closed socket proves the same thing and keeps the output readable.
test "$request_status" -ne 0 ; check "and the hung client was cut off" $?

# --- the deadline is a deadline ----------------------------------------------
"$PY" -m {{ package_name }} serve --port "$((PORT + 2))" --drain-timeout 0.3 >"$log" 2>&1 &
server=$!
wait_for "$log" "listening"
get "$((PORT + 2))" "/work?ms=5000" >"$body" 2>&1 &
request=$!
sleep 0.2
kill -TERM "$server"

set +e
wait "$server"
status=$?
wait "$request"
request_status=$?
set -e

test "$status" -eq 1 ; check "an unfinished request exits 1" $?
grep -q "drain timeout after 0.3s" "$log" ; check "the timeout is reported with its value" $?
test "$request_status" -ne 0 ; check "and the abandoned request did not complete" $?

# --- the logic checks itself --------------------------------------------------
"$PY" -m {{ package_name }} selftest >/dev/null ; check "selftest passes" $?
"$PY" -m {{ package_name }} --version | grep -q "{{ npm_name }}" ; check "version prints" $?

if [ "$failures" -ne 0 ]; then
  printf 'smoke: %d check(s) failed\n' "$failures"
  exit 1
fi
printf 'smoke: all checks passed\n'

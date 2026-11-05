#!/usr/bin/env bash
# End-to-end checks for the write-ahead-log key/value service.
set -eu

ROOT=$(cd "$(dirname "$0")" && pwd)
PORT="${PORT:-5491}"
HOST=127.0.0.1
BIN="${BIN:-$ROOT/build/{{ npm_name }}}"
LOG=".wal-cache.log"
BASE="http://$HOST:$PORT"

checks=0
failures=0

check() {
    name=$1
    want=$2
    got=$3
    checks=$((checks + 1))
    if [ "$want" = "$got" ]; then
        echo "ok - $name"
        return
    fi
    failures=$((failures + 1))
    echo "FAIL - $name: want '$want' got '$got'"
}

contains() {
    name=$1
    needle=$2
    haystack=$3
    checks=$((checks + 1))
    case "$haystack" in
        *"$needle"*) echo "ok - $name" ;;
        *)
            failures=$((failures + 1))
            echo "FAIL - $name: '$needle' missing from '$haystack'"
            ;;
    esac
}

listening() {
    curl -fsS --max-time 1 "$BASE/health" >/dev/null 2>&1
}

if listening; then
    echo "port $PORT is already answering - stop that process before running this step"
    exit 1
fi

if [ ! -x "$BIN" ]; then
    echo "smoke: $BIN is missing - run make build first"
    exit 1
fi

work=$(mktemp -d)
server=
cleanup() {
    if [ -n "$server" ]; then
        kill -TERM "$server" 2>/dev/null || true
        for _ in $(seq 1 20); do
            kill -0 "$server" 2>/dev/null || break
            sleep 0.1
        done
        kill -KILL "$server" 2>/dev/null || true
        wait "$server" 2>/dev/null || true
    fi
    rm -rf "$work"
}
trap cleanup EXIT

start() {
    "$BIN" --dir "$work/wal" --addr "$HOST:$PORT" >"$LOG" 2>&1 &
    server=$!
    tried=0
    while [ "$tried" -lt 160 ]; do
        if listening; then
            return 0
        fi
        if ! kill -0 "$server" 2>/dev/null; then
            echo "smoke: the server exited before it listened"
            cat "$LOG"
            exit 1
        fi
        tried=$((tried + 1))
        sleep 0.25
    done
    echo "smoke: the server never listened on $PORT"
    cat "$LOG"
    exit 1
}

stop() {
    kill -TERM "$server" 2>/dev/null || true
    wait "$server" 2>/dev/null || true
    server=
}

start

status=$(curl -sS --max-time 2 -o "$work/health.json" -w '%{http_code}' "$BASE/health")
check "health answers 200" 200 "$status"
contains "health counts keys" '"keys":0' "$(cat "$work/health.json")"

status=$(curl -sS --max-time 2 -o "$work/put.json" -w '%{http_code}' -X PUT --data-binary 'hello' "$BASE/kv/greeting")
check "put answers 201" 201 "$status"
contains "put echoes the key" '"key":"greeting"' "$(cat "$work/put.json")"

check "get returns the value" hello "$(curl -sS --max-time 2 "$BASE/kv/greeting")"

status=$(curl -sS --max-time 2 -o "$work/missing.json" -w '%{http_code}' "$BASE/kv/absent")
check "a missing key answers 404" 404 "$status"
contains "the 404 names the key" '"key":"absent"' "$(cat "$work/missing.json")"

status=$(curl -sS --max-time 2 -o /dev/null -w '%{http_code}' -X PATCH "$BASE/kv/greeting")
check "an unsupported method answers 405" 405 "$status"

status=$(curl -sS --max-time 2 -o "$work/nope.json" -w '%{http_code}' "$BASE/nope")
check "an unknown route answers 404" 404 "$status"
contains "the unknown route names both parts" 'no route for GET /nope' "$(cat "$work/nope.json")"

python3 -c 'import sys; sys.stdout.write("x" * 70000)' >"$work/big.txt"
status=$(curl -sS --max-time 5 -o "$work/big.json" -w '%{http_code}' -X PUT --data-binary @"$work/big.txt" "$BASE/kv/big")
check "an oversized value answers 413" 413 "$status"
contains "the 413 explains itself" 'value_too_large' "$(cat "$work/big.json")"

long=$(python3 -c 'print("k" * 257, end="")')
status=$(curl -sS --max-time 2 -o /dev/null -w '%{http_code}' -X PUT --data-binary 'x' "$BASE/kv/$long")
check "an over-long key answers 400" 400 "$status"

status=$(curl -sS --max-time 2 -o "$work/wal.json" -w '%{http_code}' "$BASE/wal")
check "the wal endpoint answers 200" 200 "$status"
contains "the wal body counts the record" '"records":1' "$(cat "$work/wal.json")"

status=$(curl -sS --max-time 2 -o "$work/compact.json" -w '%{http_code}' -X POST "$BASE/compact")
check "compaction answers 200" 200 "$status"
contains "compaction reports one live key" '"after":1' "$(cat "$work/compact.json")"

status=$(curl -sS --max-time 2 -o /dev/null -w '%{http_code}' -X DELETE "$BASE/kv/greeting")
check "delete answers 204" 204 "$status"
status=$(curl -sS --max-time 2 -o /dev/null -w '%{http_code}' -X DELETE "$BASE/kv/greeting")
check "deleting twice answers 404" 404 "$status"

check "a second key is stored" 201 "$(curl -sS --max-time 2 -o /dev/null -w '%{http_code}' -X PUT --data-binary 'kept' "$BASE/kv/durable")"

stop
start
check "the value survives a restart" kept "$(curl -sS --max-time 2 "$BASE/kv/durable")"
contains "the replayed log counts two records" '"records":3' "$(curl -sS --max-time 2 "$BASE/wal")"
stop

segments=$(find "$work/wal" -name 'wal-*.log' | wc -l | tr -d ' ')
check "the write-ahead log has one segment" 1 "$segments"

if [ "$failures" -ne 0 ]; then
    echo "smoke: $failures check(s) failed"
    exit 1
fi
echo "smoke: $checks checks, 0 failed"

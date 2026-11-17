#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5514}"
BASE="http://127.0.0.1:$PORT"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
fail=0
server=""

cleanup() {
  rm -rf "$work"
  if [ -n "${server:-}" ]; then
    kill -TERM "$server" 2>/dev/null || true
    for _ in $(seq 1 20); do kill -0 "$server" 2>/dev/null || break; sleep 0.1; done
    kill -KILL "$server" 2>/dev/null || true
    wait "$server" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1; then
  echo "port $PORT is already answering - stop that process before running this step"
  exit 1
fi

cd "$ROOT"

run() {
  set +e
  OUT=$("$@" 2>&1)
  STATUS=$?
  set -e
}

run cargo fmt --check
if [ "$STATUS" -eq 0 ]; then echo "ok   cargo fmt"; else echo "FAIL cargo fmt"; fail=1; fi

run cargo clippy --all-targets -- -D warnings
if [ "$STATUS" -eq 0 ]; then echo "ok   cargo clippy"; else echo "FAIL cargo clippy"; fail=1; printf '%s\n' "$OUT" | tail -8; fi

run cargo test
if [ "$STATUS" -eq 0 ]; then echo "ok   cargo test"; else echo "FAIL cargo test"; fail=1; printf '%s\n' "$OUT" | tail -8; fi

run cargo build --release
if [ "$STATUS" -eq 0 ]; then echo "ok   cargo build --release"; else echo "FAIL cargo build --release"; fail=1; printf '%s\n' "$OUT" | tail -8; fi

if [ -x ./target/release/{{ npm_name }} ]; then
  PORT="$PORT" ./target/release/{{ npm_name }} >"$work/server.log" 2>&1 &
  server=$!
  ready=0
  i=0
  while [ "$i" -lt 160 ]; do
    if curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1; then ready=1; break; fi
    i=$((i + 1))
    sleep 0.25
  done
  kill -0 "$server" 2>/dev/null || { echo "FAIL server died"; cat "$work/server.log"; exit 1; }
  if [ "$ready" -eq 1 ]; then
    echo "ok   server becomes ready"
    body="$(curl -sS --max-time 5 "$BASE/health")"
    if printf '%s' "$body" | grep -Fq '"status":"ok"'; then echo "ok   health body"; else echo "FAIL health body"; fail=1; fi
    # assert JSON log lines
    if grep -Fq '"health check served"' "$work/server.log"; then echo "ok   log line emitted"; else echo "FAIL log line emitted"; fail=1; fi
    if grep -Fq '"level":"INFO"' "$work/server.log"; then echo "ok   json level field"; else echo "FAIL json level field"; fail=1; fi
    if grep -Fq '"listening"' "$work/server.log"; then echo "ok   startup log"; else echo "FAIL startup log"; fail=1; fi
  else
    echo "FAIL server becomes ready"
    cat "$work/server.log" >&2 || true
    fail=1
  fi
  kill "$server" 2>/dev/null || true
  wait "$server" 2>/dev/null || true
  server=""
  trap - EXIT
  rm -rf "$work"
else
  echo "FAIL release binary exists"
  fail=1
fi

[ "$fail" -eq 0 ] || { echo "smoke: FAILED"; exit 1; }
echo "smoke: all checks passed"
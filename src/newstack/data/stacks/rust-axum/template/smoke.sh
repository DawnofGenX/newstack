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

if ! command -v cargo >/dev/null 2>&1; then
  echo "smoke: cargo is missing (install rust)"
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "smoke: curl is missing (install curl)"
  exit 1
fi

echo "smoke: rust-axum"

run cargo fmt --check
if [ "$STATUS" -eq 0 ]; then ok "cargo fmt"; else bad "cargo fmt"; printf '%s\n' "$OUT" | tail -8; fi

run cargo clippy --all-targets -- -D warnings
if [ "$STATUS" -eq 0 ]; then ok "cargo clippy"; else bad "cargo clippy"; printf '%s\n' "$OUT" | tail -8; fi

run cargo test
if [ "$STATUS" -eq 0 ]; then ok "cargo test"; else bad "cargo test"; printf '%s\n' "$OUT" | tail -8; fi

run cargo build --release
if [ "$STATUS" -eq 0 ]; then ok "cargo build --release"; else bad "cargo build --release"; printf '%s\n' "$OUT" | tail -8; fi

PORT=18092
BASE="http://127.0.0.1:${PORT}"
work=$(mktemp -d)
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

if [ -x ./target/release/{{ npm_name }} ]; then
  PORT="$PORT" ./target/release/{{ npm_name }} >"$work/server.log" 2>&1 &
  srv=$!
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

    code=$(curl --max-time 10 -s -o "$work/create.json" -w '%{http_code}' -X POST -H 'content-type: application/json' -d '{"name":"smoke"}' "${BASE}/items")
    if [ "$code" = "201" ]; then ok "POST /items returns 201"; else bad "POST /items returns 201"; fi
  else
    bad "server becomes ready"
    cat "$work/server.log" >&2 || true
  fi
  kill "$srv" 2>/dev/null || true
  wait "$srv" 2>/dev/null || true
  srv=""
  trap - EXIT
  rm -rf "$work"
else
  bad "release binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
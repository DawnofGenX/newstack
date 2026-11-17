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

if ! command -v go >/dev/null 2>&1; then
  echo "smoke: go is missing (install go)"
  exit 1
fi
if ! command -v make >/dev/null 2>&1; then
  echo "smoke: make is missing (install make)"
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "smoke: curl is missing (install curl)"
  exit 1
fi

echo "smoke: go-jwt-api"

run make build
if [ "$STATUS" -eq 0 ]; then ok "make build"; else bad "make build"; printf '%s\n' "$OUT" | tail -8; fi

run make test
if [ "$STATUS" -eq 0 ]; then ok "make test"; else bad "make test"; printf '%s\n' "$OUT" | tail -8; fi

run ./build/{{ npm_name }} --selftest
if [ "$STATUS" -eq 0 ]; then ok "selftest passes"; else bad "selftest passes"; printf '%s\n' "$OUT" | tail -8; fi

PORT=18091
BASE="http://127.0.0.1:${PORT}"
work=$(mktemp -d)
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

if [ -x ./build/{{ npm_name }} ]; then
  TOKEN_SECRET=smoke-secret PORT="$PORT" ./build/{{ npm_name }} --db "$work/users.json" >"$work/server.log" 2>&1 &
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

    code=$(curl --max-time 10 -s -o "$work/reg.json" -w '%{http_code}' -X POST -H 'content-type: application/json' -d '{"email":"ada@example.com","password":"correct horse"}' "${BASE}/register")
    if [ "$code" = "201" ]; then ok "register returns 201"; else bad "register returns 201"; fi

    code=$(curl --max-time 10 -s -o "$work/login.json" -w '%{http_code}' -X POST -H 'content-type: application/json' -d '{"email":"ada@example.com","password":"correct horse"}' "${BASE}/login")
    if [ "$code" = "200" ]; then ok "login returns 200"; else bad "login returns 200"; fi
    if grep -q '"token"' "$work/login.json" 2>/dev/null; then ok "login returns token"; else bad "login returns token"; fi
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
  bad "built binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
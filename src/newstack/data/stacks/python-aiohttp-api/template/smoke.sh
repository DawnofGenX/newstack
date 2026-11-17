#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5500}"
BASE="http://127.0.0.1:${PORT}"
SERVER_PID=""

cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

.venv/bin/python -m {{ package_name }} &
SERVER_PID=$!

for _ in $(seq 1 50); do
  if curl -sS "${BASE}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

fail() {
  echo " FAIL: $*" >&2
  exit 1
}

code="$(curl -sS -o /tmp/smoke_body -w '%{http_code}' "${BASE}/health")"
[[ "$code" == "200" ]] || fail "health expected 200 got $code"
grep -q '"status": "ok"' /tmp/smoke_body || fail "health body"

code="$(curl -sS -o /tmp/smoke_body -w '%{http_code}' "${BASE}/stats?text=hello%20world")"
[[ "$code" == "200" ]] || fail "stats expected 200 got $code"
grep -q '"words": 2' /tmp/smoke_body || fail "stats body"

code="$(curl -sS -o /tmp/smoke_body -w '%{http_code}' "${BASE}/stats")"
[[ "$code" == "422" ]] || fail "missing text expected 422 got $code"

echo "smoke ok"
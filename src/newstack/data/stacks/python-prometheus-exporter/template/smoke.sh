#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-5501}"
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
  if curl -sS "${BASE}/metrics" >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

fail() {
  echo " FAIL: $*" >&2
  exit 1
}

code="$(curl -sS -o /tmp/smoke_body -w '%{http_code}' "${BASE}/metrics")"
[[ "$code" == "200" ]] || fail "metrics expected 200 got $code"
grep -q '# TYPE app_up gauge' /tmp/smoke_body || fail "missing metric type"
grep -q 'app_up 1' /tmp/smoke_body || fail "missing metric value"
ct="$(curl -sS -D - -o /dev/null "${BASE}/metrics" | tr -d '\r' | awk -F': ' 'tolower($1)=="content-type"{print $2}')"
echo "$ct" | grep -q 'text/plain' || fail "bad content-type: $ct"

echo "smoke ok"
#!/usr/bin/env bash
# Build the image, wait for the container to be healthy, then ask it real questions.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
port="${SMOKE_PORT:-18080}"
export PORT="$port"

cleanup() { docker compose down --remove-orphans >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker compose up -d --build --wait

fail=0
check() {
  local label="$1" url="$2" want="$3" body status
  body="$(curl -fsS "http://127.0.0.1:$port$url")" || status=$?
  if [[ "${status:-0}" -ne 0 ]]; then
    printf 'FAIL %s: curl exited %s\n' "$label" "${status:-0}"
    fail=1
    return
  fi
  if grep -qF -- "$want" <<<"$body"; then
    printf 'ok   %s: %s\n' "$label" "$want"
  else
    printf 'FAIL %s: expected %q in %q\n' "$label" "$want" "$body"
    fail=1
  fi
}

check health   /health   '"status": "ok"'
check root     /        '/health'
check metrics  /metrics 'requests_total'

status=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$port/nope")
if [[ "$status" == "404" ]]; then
  printf 'ok   unknown path: 404\n'
else
  printf 'FAIL unknown path: want 404 got %s\n' "$status"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  docker compose logs --tail 40 || true
  exit 1
fi
echo "smoke: all checks passed"

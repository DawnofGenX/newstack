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

if ! command -v nim >/dev/null 2>&1; then
  echo "smoke: nim is missing (install nim)"
  exit 1
fi
if ! command -v nimble >/dev/null 2>&1; then
  echo "smoke: nimble is missing (install nimble)"
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "smoke: curl is missing (install curl)"
  exit 1
fi

echo "smoke: nim-http-api"

run nimble build -d:release
if [ "$STATUS" -eq 0 ]; then ok "nimble build"; else bad "nimble build"; printf '%s\n' "$OUT" | tail -8; fi

run nimble test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

run nim check --hints:off src/{{ package_name }}.nim
if [ "$STATUS" -eq 0 ]; then ok "nim check"; else bad "nim check"; printf '%s\n' "$OUT" | tail -8; fi

PORT=5415
BASE="http://127.0.0.1:${PORT}"
bin="./{{ package_name }}"
if [ ! -x "$bin" ]; then bad "binary exists"; printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"; [ "$FAILED" -eq 0 ]; exit $?; fi
ok "binary exists"

work=$(mktemp -d)
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

if curl -fsS --max-time 2 "${BASE}/health" >/dev/null 2>&1; then
  bad "port free"
else
  ok "port free"
  PORT="$PORT" "$bin" >"$work/server.log" 2>&1 &
  srv=$!
  ready=1
  i=0
  while [ "$i" -lt 120 ]; do
    if curl --max-time 2 -fsS "${BASE}/health" >/dev/null 2>&1; then ready=0; break; fi
    i=$((i + 1))
    sleep 0.5
  done
  if [ "$ready" -eq 0 ]; then
    ok "server becomes ready"
    health=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' "${BASE}/health")
    if [ "$health" = "200" ]; then ok "health status"; else bad "health status"; fi

    stats=$(curl --max-time 10 -s "${BASE}/stats?text=hello%20world%0A" || true)
    printf '%s' "$stats" | grep -q '"lines":1' && ok "stats lines" || bad "stats lines"
    printf '%s' "$stats" | grep -q '"bytes":12' && ok "stats bytes" || bad "stats bytes"

    posted=$(curl --max-time 10 -s -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' "${BASE}/stats" || true)
    printf '%s' "$posted" | grep -q '"words":3' && ok "post words" || bad "post words"

    badcode=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' "${BASE}/stats")
    if [ "$badcode" = "422" ]; then ok "missing 422"; else bad "missing 422"; fi

    missing=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' "${BASE}/nope")
    if [ "$missing" = "404" ]; then ok "unknown 404"; else bad "unknown 404"; fi
  else
    bad "server becomes ready"
    cat "$work/server.log" >&2 || true
  fi
  kill "$srv" 2>/dev/null || true
  wait "$srv" 2>/dev/null || true
  srv=""
fi

trap - EXIT
rm -rf "$work"

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
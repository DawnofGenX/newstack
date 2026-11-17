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

if ! command -v g++ >/dev/null 2>&1 && ! command -v c++ >/dev/null 2>&1; then
  echo "smoke: g++ is missing (install g++)"
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

echo "smoke: cpp-http-api"

run make
if [ "$STATUS" -eq 0 ]; then ok "make builds"; else bad "make builds"; printf '%s\n' "$OUT" | tail -8; fi

run make test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

PORT=5438
BASE="http://127.0.0.1:${PORT}"
bin="./build/{{ npm_name }}"
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
  ready=0
  i=0
  while [ "$i" -lt 240 ]; do
    if curl --max-time 2 -fsS "${BASE}/health" >/dev/null 2>&1; then ready=1; break; fi
    i=$((i + 1))
    sleep 0.5
  done
  if [ "$ready" -eq 1 ]; then
    ok "server becomes ready"
    health=$(curl --max-time 10 -sS "${BASE}/health" || true)
    if [ "$health" = '{"status":"ok"}' ]; then ok "health body"; else bad "health body"; fi

    get=$(curl --max-time 10 -sS "${BASE}/stats?text=hello%20world%0A" || true)
    printf '%s' "$get" | grep -q '"lines":1' && ok "GET stats lines" || bad "GET stats lines"
    printf '%s' "$get" | grep -q '"bytes":12' && ok "GET stats bytes" || bad "GET stats bytes"

    posted=$(curl --max-time 10 -sS -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' "${BASE}/stats" || true)
    printf '%s' "$posted" | grep -q '"words":3' && ok "POST stats words" || bad "POST stats words"

    missing=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' "${BASE}/stats")
    if [ "$missing" = "422" ]; then ok "missing text 422"; else bad "missing text 422"; fi

    broken=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' -X POST -H 'content-type: application/json' --data-binary 'nope' "${BASE}/stats")
    if [ "$broken" = "422" ]; then ok "invalid json 422"; else bad "invalid json 422"; fi

    number=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' -X POST -H 'content-type: application/json' --data-binary '{"text":42}' "${BASE}/stats")
    if [ "$number" = "422" ]; then ok "non-string text 422"; else bad "non-string text 422"; fi

    gone=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' "${BASE}/nope")
    if [ "$gone" = "404" ]; then ok "unknown route 404"; else bad "unknown route 404"; fi

    wrong=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' -X DELETE "${BASE}/health")
    if [ "$wrong" = "405" ]; then ok "wrong method 405"; else bad "wrong method 405"; fi
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
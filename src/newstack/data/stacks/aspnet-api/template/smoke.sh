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

if ! command -v dotnet >/dev/null 2>&1; then
  echo "smoke: dotnet is missing (install dotnet)"
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "smoke: curl is missing (install curl)"
  exit 1
fi

echo "smoke: aspnet-api"

run dotnet test --nologo
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

run dotnet build --nologo -warnaserror
if [ "$STATUS" -eq 0 ]; then ok "dotnet build"; else bad "dotnet build"; printf '%s\n' "$OUT" | tail -8; fi

PORT=5199
BASE="http://127.0.0.1:${PORT}"
dll="bin/Debug/net8.0/{{ npm_name }}.dll"
if [ ! -f "$dll" ]; then bad "build output exists"; printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"; [ "$FAILED" -eq 0 ]; exit $?; fi
ok "build output exists"

work=$(mktemp -d)
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

if curl -fsS --max-time 2 "${BASE}/health" >/dev/null 2>&1; then
  bad "port free"
else
  ok "port free"
  dotnet "$dll" --urls "${BASE}" >"$work/server.log" 2>&1 &
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

    body=$(curl --max-time 10 -fsS "${BASE}/stats?text=hello%20world%0A" || true)
    printf '%s' "$body" | grep -q '"lines":1' && ok "GET stats lines" || bad "GET stats lines"
    printf '%s' "$body" | grep -q '"bytes":12' && ok "GET stats bytes" || bad "GET stats bytes"

    post=$(curl --max-time 10 -fsS -X POST -H 'content-type: application/json' -d '{"text":"a b\nc\n"}' "${BASE}/stats" || true)
    printf '%s' "$post" | grep -q '"words":3' && ok "POST stats words" || bad "POST stats words"

    missing=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' -X POST -H 'content-type: application/json' -d '{}' "${BASE}/stats")
    if [ "$missing" = "422" ]; then ok "missing text 422"; else bad "missing text 422"; fi

    unknown=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' "${BASE}/nope")
    if [ "$unknown" = "404" ]; then ok "unknown route 404"; else bad "unknown route 404"; fi
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
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

echo "smoke: fsharp-http-api"

run dotnet build {{ npm_name }}.fsproj --nologo
if [ "$STATUS" -eq 0 ]; then ok "dotnet build"; else bad "dotnet build"; printf '%s\n' "$OUT" | tail -8; fi

dll="bin/Debug/net8.0/{{ npm_name }}.dll"
if [ -f "$dll" ]; then
  run dotnet "$dll" --selftest
  if [ "$STATUS" -eq 0 ]; then ok "selftest passes"; else bad "selftest passes"; printf '%s\n' "$OUT" | tail -8; fi
else
  bad "build output exists"
fi

PORT=5446
BASE="http://127.0.0.1:${PORT}"
work=$(mktemp -d)
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

if curl -fsS --max-time 2 "${BASE}/health" >/dev/null 2>&1; then
  bad "port free"
else
  ok "port free"
  PORT="$PORT" dotnet "$dll" >"$work/server.log" 2>&1 &
  srv=$!
  ready=1
  i=0
  while [ "$i" -lt 160 ]; do
    if curl --max-time 2 -fsS "${BASE}/health" >/dev/null 2>&1; then ready=0; break; fi
    i=$((i + 1))
    sleep 0.25
  done
  if [ "$ready" -eq 0 ]; then
    ok "server becomes ready"
    health=$(curl --max-time 10 -fsS "${BASE}/health" || true)
    if [ "$health" = '{"status":"ok"}' ]; then ok "health body"; else bad "health body"; fi

    get=$(curl --max-time 10 -fsS "${BASE}/stats?text=hello%20world%0A" || true)
    if [ "$get" = '{"text":"hello world\n","lines":1,"words":2,"bytes":12}' ]; then ok "GET stats"; else bad "GET stats"; printf '       got: %s\n' "$get"; fi

    post=$(curl --max-time 10 -fsS -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' "${BASE}/stats" || true)
    if printf '%s' "$post" | grep -q '"words":3'; then ok "POST stats"; else bad "POST stats"; fi

    missing=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' -X POST -H 'content-type: application/json' --data-binary '{}' "${BASE}/stats")
    if [ "$missing" = "422" ]; then ok "missing text 422"; else bad "missing text 422"; fi

    unknown=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' "${BASE}/nope")
    if [ "$unknown" = "404" ]; then ok "unknown route 404"; else bad "unknown route 404"; fi

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
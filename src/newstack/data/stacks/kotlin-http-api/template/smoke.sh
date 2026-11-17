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

if ! command -v java >/dev/null 2>&1; then
  echo "smoke: java is missing (install java)"
  exit 1
fi
if ! command -v mvn >/dev/null 2>&1; then
  echo "smoke: mvn is missing (install maven)"
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "smoke: curl is missing (install curl)"
  exit 1
fi

echo "smoke: kotlin-http-api"

run mvn -q -B -DskipTests package
if [ "$STATUS" -eq 0 ]; then ok "mvn package"; else bad "mvn package"; printf '%s\n' "$OUT" | tail -8; fi

if [ -f target/{{ npm_name }}.jar ]; then
  run java -jar target/{{ npm_name }}.jar --selftest
  if [ "$STATUS" -eq 0 ]; then ok "selftest passes"; else bad "selftest passes"; printf '%s\n' "$OUT" | tail -8; fi

  PORT=18100
  BASE="http://127.0.0.1:${PORT}"
  work=$(mktemp -d)
  srv=""
  trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

  PORT="$PORT" java -jar target/{{ npm_name }}.jar >"$work/server.log" 2>&1 &
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
    if [ "$health" = '{"status":"ok"}' ]; then ok "health body"; else bad "health body"; fi

    stats=$(curl --max-time 10 -fsS "${BASE}/stats?text=hello%20world%0A" || true)
    if printf '%s' "$stats" | grep -q '"lines":1'; then ok "stats body"; else bad "stats body"; fi
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
  bad "jar exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
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

if ! command -v go >/dev/null 2>&1; then echo "smoke: go missing"; exit 1; fi
if ! command -v curl >/dev/null 2>&1; then echo "smoke: curl missing"; exit 1; fi

echo "smoke: go-rate-limiter"

run go vet ./...
if [ "$STATUS" -eq 0 ]; then ok "go vet passes"; else bad "go vet passes"; printf '%s\n' "$OUT" | tail -8; fi

run go test ./...
if [ "$STATUS" -eq 0 ]; then ok "go test passes"; else bad "go test passes"; printf '%s\n' "$OUT" | tail -8; fi

run go build -o bin/server .
if [ "$STATUS" -eq 0 ]; then ok "go build"; else bad "go build"; printf '%s\n' "$OUT" | tail -8; fi

PORT=5540
BASE="http://127.0.0.1:${PORT}"
work=$(mktemp -d)
srv=""
trap 'if [ -n "$srv" ]; then kill "$srv" 2>/dev/null || true; wait "$srv" 2>/dev/null || true; fi; rm -rf "$work"' EXIT

if [ -x ./bin/server ]; then
  PORT="$PORT" ./bin/server >"$work/server.log" 2>&1 &
  srv=$!
  ready=0
  i=0
  while [ "$i" -lt 60 ]; do
    code=$(curl --max-time 2 -sS -o /dev/null -w '%{http_code}' "${BASE}/health" 2>/dev/null || true)
    if [ "$code" = "200" ]; then ready=1; break; fi
    i=$((i + 1))
    sleep 0.5
  done
  if [ "$ready" -eq 1 ]; then
    ok "server becomes ready"
    # exhaust burst then expect 429
    got429=0
    for j in 1 2 3 4 5; do
      code=$(curl --max-time 10 -sS -o /dev/null -w '%{http_code}' "${BASE}/limited" 2>/dev/null || true)
      if [ "$code" = "429" ]; then got429=1; break; fi
    done
    if [ "$got429" -eq 1 ]; then
      ok "rate limiter returns 429"
    else
      bad "rate limiter returns 429"
    fi
    # Retry-After header present on a 429
    headers=$(curl --max-time 10 -sS -D - -o /dev/null "${BASE}/limited" 2>/dev/null || true)
    if printf '%s' "$headers" | grep -qi 'Retry-After:'; then ok "Retry-After header"; else bad "Retry-After header"; fi
  else
    bad "server becomes ready"
    cat "$work/server.log" >&2 || true
  fi
  kill "$srv" 2>/dev/null || true
  wait "$srv" 2>/dev/null || true
  srv=""
else
  bad "server binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

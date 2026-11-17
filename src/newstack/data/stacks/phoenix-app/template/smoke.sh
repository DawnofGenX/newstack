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

if ! command -v curl >/dev/null 2>&1; then
  echo "smoke: curl is missing (install curl)"
  exit 1
fi
if ! command -v mix >/dev/null 2>&1; then
  echo "smoke: mix is missing (install mix)"
  exit 1
fi

echo "smoke: phoenix-app"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cat > "$work/step_0.sh" <<'__STEP__'
mix deps.get
__STEP__
run sh "$work/step_0.sh"
if [ "$STATUS" -eq 0 ]; then ok "deps"; else bad "deps"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_1.sh" <<'__STEP__'
mix format --check-formatted
__STEP__
run sh "$work/step_1.sh"
if [ "$STATUS" -eq 0 ]; then ok "format"; else bad "format"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_2.sh" <<'__STEP__'
mix test
__STEP__
run sh "$work/step_2.sh"
if [ "$STATUS" -eq 0 ]; then ok "test"; else bad "test"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_3.sh" <<'__STEP__'
if curl -sS --max-time 2 http://127.0.0.1:5417/health >/dev/null 2>&1; then echo 'port 5417 is already answering - stop that process before running this step'; exit 1; fi; PORT=5417 mix phx.server >.phx.log 2>&1 & srv=$!; ok=1; for _ in $(seq 1 240); do if curl --max-time 2 -sS http://127.0.0.1:5417/health >/dev/null 2>&1; then ok=0; break; fi; sleep 0.5; done; kill -0 $srv 2>/dev/null || { echo 'the server exited before it answered'; exit 1; }; if [ $ok -ne 0 ]; then cat .phx.log; kill $srv 2>/dev/null; exit 1; fi; body=$(curl --max-time 10 -sS 'http://127.0.0.1:5417/stats?text=hello%20world%0A'); missing=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' http://127.0.0.1:5417/stats); unknown=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5417/nope); kill $srv 2>/dev/null; wait $srv 2>/dev/null; rm -f .phx.log; printf 'get=%s\nmissing=%s unknown=%s\n' "$body" "$missing" "$unknown"; test "$missing" = 422; test "$unknown" = 404; echo "$body" | grep -q '"lines":1'; echo "$body" | grep -q '"bytes":12'
__STEP__
run sh "$work/step_3.sh"
if [ "$STATUS" -eq 0 ]; then ok "http"; else bad "http"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

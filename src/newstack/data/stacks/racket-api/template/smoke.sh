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
if ! command -v racket >/dev/null 2>&1; then
  echo "smoke: racket is missing (install racket)"
  exit 1
fi

echo "smoke: racket-api"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cat > "$work/step_0.sh" <<'__STEP__'
raco make src/server.rkt src/contract.rkt src/counts.rkt
__STEP__
run sh "$work/step_0.sh"
if [ "$STATUS" -eq 0 ]; then ok "compile"; else bad "compile"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_1.sh" <<'__STEP__'
racket tests/run-tests.rkt
__STEP__
run sh "$work/step_1.sh"
if [ "$STATUS" -eq 0 ]; then ok "test"; else bad "test"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_2.sh" <<'__STEP__'
set -e
if curl -fsS --max-time 2 http://127.0.0.1:5429/health >/dev/null 2>&1; then echo 'port 5429 is already answering - stop that process before running this step'; exit 1; fi
PORT=5429 racket src/server.rkt > .racket.log 2>&1 &
server=$!
trap 'kill -TERM -"$server" 2>/dev/null || kill $server 2>/dev/null || true; wait $server 2>/dev/null || true' EXIT
kill -0 $server 2>/dev/null || { cat .racket.log; echo 'the service exited before it answered'; exit 1; }
ok=0
for _ in $(seq 1 120); do
  if curl -fsS --max-time 2 http://127.0.0.1:5429/health >/dev/null 2>&1; then ok=1; break; fi
  sleep 0.5
done
if [ $ok -ne 1 ]; then echo 'the service never answered'; cat .racket.log; kill $server 2>/dev/null || true; exit 1; fi
health=$(curl -sS --max-time 10 http://127.0.0.1:5429/health)
test "$health" = '{"status":"ok"}'
get=$(curl -sS --max-time 10 'http://127.0.0.1:5429/stats?text=hello%20world%0A')
printf '%s' "$get" | grep -q '"lines":1'
printf '%s' "$get" | grep -q '"bytes":12'
posted=$(curl -sS --max-time 10 -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5429/stats)
printf '%s' "$posted" | grep -q '"words":3'
missing=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:5429/stats)
test "$missing" = 422
broken=$(curl -sS --max-time 10 -H 'content-type: application/json' --data-binary 'nope' http://127.0.0.1:5429/stats)
printf '%s' "$broken" | grep -q 'invalid_json'
gone=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:5429/nope)
test "$gone" = 404
kill $server 2>/dev/null || true
wait $server 2>/dev/null || true
__STEP__
run sh "$work/step_2.sh"
if [ "$STATUS" -eq 0 ]; then ok "http"; else bad "http"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

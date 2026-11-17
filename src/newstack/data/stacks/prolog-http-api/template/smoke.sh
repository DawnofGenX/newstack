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
if ! command -v swipl >/dev/null 2>&1; then
  echo "smoke: swipl is missing (install swipl)"
  exit 1
fi

echo "smoke: prolog-http-api"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cat > "$work/step_0.sh" <<'__STEP__'
swipl -q tests/run-tests.pl
__STEP__
run sh "$work/step_0.sh"
if [ "$STATUS" -eq 0 ]; then ok "test"; else bad "test"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_1.sh" <<'__STEP__'
set -e
if curl -fsS --max-time 2 http://127.0.0.1:5430/health >/dev/null 2>&1; then echo 'port 5430 is already answering - stop that process before running this step'; exit 1; fi
PORT=5430 swipl -q src/server.pl > .prolog.log 2>&1 &
server=$!
trap 'kill -TERM -"$server" 2>/dev/null || kill $server 2>/dev/null || true; wait $server 2>/dev/null || true' EXIT
kill -0 $server 2>/dev/null || { cat .prolog.log; echo 'the service exited before it answered'; exit 1; }
ok=0
for _ in $(seq 1 120); do
  if curl -fsS --max-time 2 http://127.0.0.1:5430/health >/dev/null 2>&1; then ok=1; break; fi
  sleep 0.5
done
if [ $ok -ne 1 ]; then echo 'the service never answered'; cat .prolog.log; kill $server 2>/dev/null || true; exit 1; fi
health=$(curl -sS --max-time 10 http://127.0.0.1:5430/health)
test "$health" = '{"status":"ok"}'
get=$(curl -sS --max-time 10 'http://127.0.0.1:5430/stats?text=hello%20world%0A')
printf '%s' "$get" | grep -q '"lines":1'
printf '%s' "$get" | grep -q '"bytes":12'
posted=$(curl -sS --max-time 10 -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5430/stats)
printf '%s' "$posted" | grep -q '"words":3'
missing=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:5430/stats)
test "$missing" = 422
broken=$(curl -sS --max-time 10 -H 'content-type: application/json' --data-binary 'nope' http://127.0.0.1:5430/stats)
printf '%s' "$broken" | grep -q 'invalid_json'
gone=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:5430/nope)
test "$gone" = 404
kill $server 2>/dev/null || true
wait $server 2>/dev/null || true
__STEP__
run sh "$work/step_1.sh"
if [ "$STATUS" -eq 0 ]; then ok "http"; else bad "http"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

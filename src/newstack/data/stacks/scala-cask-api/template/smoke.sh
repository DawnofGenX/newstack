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
if ! command -v java >/dev/null 2>&1; then
  echo "smoke: java is missing (install java)"
  exit 1
fi
if ! command -v scala-cli >/dev/null 2>&1; then
  echo "smoke: scala-cli is missing (install scala-cli)"
  exit 1
fi

echo "smoke: scala-cask-api"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cat > "$work/step_0.sh" <<'__STEP__'
scala-cli fmt --check .
__STEP__
run sh "$work/step_0.sh"
if [ "$STATUS" -eq 0 ]; then ok "format"; else bad "format"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_1.sh" <<'__STEP__'
scala-cli test .
__STEP__
run sh "$work/step_1.sh"
if [ "$STATUS" -eq 0 ]; then ok "test"; else bad "test"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_2.sh" <<'__STEP__'
mkdir -p bin && scala-cli --power package . -o bin/{{ npm_name }}.jar --assembly -f
__STEP__
run sh "$work/step_2.sh"
if [ "$STATUS" -eq 0 ]; then ok "package"; else bad "package"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_3.sh" <<'__STEP__'
set -e
if curl -fsS --max-time 2 http://127.0.0.1:5419/health >/dev/null 2>&1; then echo 'port 5419 is already answering - stop that process before running this step'; exit 1; fi; PORT=5419 java -jar bin/{{ npm_name }}.jar > .cask.log 2>&1 &
server=$!
trap 'kill -TERM -"$server" 2>/dev/null || kill $server 2>/dev/null || true; wait $server 2>/dev/null || true' EXIT
ready=1
for _ in $(seq 1 120); do
  if curl --max-time 2 -fsS http://127.0.0.1:5419/health >/dev/null 2>&1; then ready=0; break; fi
  sleep 0.5
done; kill -0 $server 2>/dev/null || { echo 'the server exited before it answered'; exit 1; };
if [ "$ready" != 0 ]; then
  cat .cask.log
  kill $server 2>/dev/null || true
  wait $server 2>/dev/null || true
  exit 1
fi
health=$(curl --max-time 10 -fsS http://127.0.0.1:5419/health)
stats=$(curl --max-time 10 -fsS 'http://127.0.0.1:5419/stats?text=hello%20world%0A')
posted=$(curl --max-time 10 -fsS -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5419/stats)
missing=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5419/stats)
broken=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' -X POST -H 'content-type: application/json' --data-binary 'nope' http://127.0.0.1:5419/stats)
gone=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5419/nope)
wrong=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' -X DELETE http://127.0.0.1:5419/health)
kill $server 2>/dev/null || true
wait $server 2>/dev/null || true
test "$health" = '{"status":"ok"}' || { echo "health: $health"; exit 1; }
printf '%s' "$stats" | grep -q '"lines":1' || { echo "stats: $stats"; exit 1; }
printf '%s' "$stats" | grep -q '"bytes":12' || { echo "stats: $stats"; exit 1; }
printf '%s' "$posted" | grep -q '"words":3' || { echo "posted: $posted"; exit 1; }
test "$missing" = 422 || { echo "missing: $missing"; exit 1; }
test "$broken" = 422 || { echo "broken: $broken"; exit 1; }
test "$gone" = 404 || { echo "gone: $gone"; exit 1; }
test "$wrong" = 405 || { echo "wrong: $wrong"; exit 1; }
echo "the service answered every check"

__STEP__
run sh "$work/step_3.sh"
if [ "$STATUS" -eq 0 ]; then ok "http"; else bad "http"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

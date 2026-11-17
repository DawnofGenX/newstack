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
if ! command -v dune >/dev/null 2>&1; then
  echo "smoke: dune is missing (install dune)"
  exit 1
fi

echo "smoke: ocaml-http-api"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cat > "$work/step_0.sh" <<'__STEP__'
dune build @all
__STEP__
run sh "$work/step_0.sh"
if [ "$STATUS" -eq 0 ]; then ok "build"; else bad "build"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_1.sh" <<'__STEP__'
dune runtest
__STEP__
run sh "$work/step_1.sh"
if [ "$STATUS" -eq 0 ]; then ok "test"; else bad "test"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_2.sh" <<'__STEP__'
set -e
if curl -fsS --max-time 2 http://127.0.0.1:5436/health >/dev/null 2>&1; then
  echo 'port 5436 is already answering - stop that process before running this step'
  exit 1
fi
PORT=5436 ./bin/{{ npm_name }} > .ocaml-http.log 2>&1 &
server=$!
trap 'kill -TERM -"$server" 2>/dev/null || kill $server 2>/dev/null || true; wait $server 2>/dev/null || true' EXIT
i=0
while [ $i -lt 120 ]; do
  if curl -fsS --max-time 2 http://127.0.0.1:5436/health >/dev/null 2>&1; then
    break
  fi
  i=$((i + 1))
  sleep 0.25
done
if [ $i -ge 120 ]; then
  cat .ocaml-http.log
  echo 'the server did not answer in time'
  exit 1
fi
kill -0 $server 2>/dev/null || { cat .ocaml-http.log; echo 'the server exited before it answered'; exit 1; }
health=$(curl -sS --max-time 10 http://127.0.0.1:5436/health)
test "$health" = '{"status":"ok"}'
get=$(curl -sS --max-time 10 'http://127.0.0.1:5436/stats?text=hello%20world%0A')
printf '%s' "$get" | grep -q '"lines":1'
printf '%s' "$get" | grep -q '"bytes":12'
posted=$(curl -sS --max-time 10 -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5436/stats)
printf '%s' "$posted" | grep -q '"words":3'
missing=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:5436/stats)
test "$missing" = 422
broken=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' -X POST -H 'content-type: application/json' --data-binary 'nope' http://127.0.0.1:5436/stats)
test "$broken" = 422
number=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' -X POST -H 'content-type: application/json' --data-binary '{"text":42}' http://127.0.0.1:5436/stats)
test "$number" = 422
gone=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:5436/nope)
test "$gone" = 404
wrong=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' -X DELETE http://127.0.0.1:5436/health)
test "$wrong" = 405
__STEP__
run sh "$work/step_2.sh"
if [ "$STATUS" -eq 0 ]; then ok "http"; else bad "http"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

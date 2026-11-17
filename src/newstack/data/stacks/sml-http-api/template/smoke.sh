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


echo "smoke: sml-http-api"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cat > "$work/step_0.sh" <<'__STEP__'
make build
__STEP__
run sh "$work/step_0.sh"
if [ "$STATUS" -eq 0 ]; then ok "build"; else bad "build"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_1.sh" <<'__STEP__'
make test
__STEP__
run sh "$work/step_1.sh"
if [ "$STATUS" -eq 0 ]; then ok "test"; else bad "test"; printf '%s\n' "$OUT" | tail -8; fi

cat > "$work/step_2.sh" <<'__STEP__'
set -e
if curl -fsS --max-time 2 http://127.0.0.1:5445/health >/dev/null 2>&1; then
  echo "port 5445 is already answering - stop that process before running this step"
  exit 1
fi
make build >/dev/null
PORT=5445 ./bin/{{ npm_name }} > .sml-http.log 2>&1 &
server=$!
trap 'kill -TERM -"$server" 2>/dev/null || kill $server 2>/dev/null || true; wait $server 2>/dev/null || true' EXIT
ready=1
for _ in $(seq 1 120); do
  if curl --max-time 2 -fsS http://127.0.0.1:5445/health >/dev/null 2>&1; then ready=0; break; fi
  sleep 0.25
done
if [ "$ready" -ne 0 ]; then cat .sml-http.log; echo "the server did not answer in time"; exit 1; fi
kill -0 $server 2>/dev/null || { cat .sml-http.log; echo "the server exited"; exit 1; }

check() {
  name=$1
  want=$2
  got=$3
  if [ "$want" != "$got" ]; then
    echo "FAIL $name: want [$want] got [$got]"
    exit 1
  fi
  echo "ok $name"
}

check health '{"status":"ok"}' "$(curl --max-time 10 -fsS http://127.0.0.1:5445/health)"
check get '{"text":"hello world\n","lines":1,"words":2,"bytes":12}' \
  "$(curl --max-time 10 -fsS 'http://127.0.0.1:5445/stats?text=hello%20world%0A')"
check utf8 '{"text":"héllo wörld\n","lines":1,"words":2,"bytes":14}' \
  "$(curl --max-time 10 -fsS 'http://127.0.0.1:5445/stats?text=h%C3%A9llo%20w%C3%B6rld%0A')"
check post '{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}' \
  "$(curl --max-time 10 -fsS -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5445/stats)"
check escape '{"text":"café","lines":0,"words":1,"bytes":5}' \
  "$(curl --max-time 10 -fsS -X POST -H 'content-type: application/json' --data-binary '{"text":"caf\u00e9"}' http://127.0.0.1:5445/stats)"
check empty '{"text":"","lines":0,"words":0,"bytes":0}' \
  "$(curl --max-time 10 -fsS 'http://127.0.0.1:5445/stats?text=')"

status() { curl --max-time 10 -s -o /dev/null -w '%{http_code}' "$@"; }
check missing_text 422 "$(status -X POST -H 'content-type: application/json' --data-binary '{}' http://127.0.0.1:5445/stats)"
check non_string 422 "$(status -X POST -H 'content-type: application/json' --data-binary '{"text":42}' http://127.0.0.1:5445/stats)"
check invalid_json 422 "$(status -X POST -H 'content-type: application/json' --data-binary 'nope' http://127.0.0.1:5445/stats)"
check unknown_route 404 "$(status http://127.0.0.1:5445/nope)"
check wrong_method 405 "$(status -X DELETE http://127.0.0.1:5445/health)"
check not_found_detail '{"error":"not_found","detail":"no route for GET /nope"}' \
  "$(curl --max-time 10 -sS http://127.0.0.1:5445/nope)"

echo "all contract checks passed"

__STEP__
run sh "$work/step_2.sh"
if [ "$STATUS" -eq 0 ]; then ok "http"; else bad "http"; printf '%s\n' "$OUT" | tail -8; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

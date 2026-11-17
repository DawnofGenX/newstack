#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v octave >/dev/null 2>&1; then
  case "octave" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: octave is missing (install octave)"; exit 1 ;;
  esac
fi
if ! command -v curl >/dev/null 2>&1; then
  case "curl" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: curl is missing (install curl)"; exit 1 ;;
  esac
fi

echo "smoke: octave-http-api"

if (
octave --no-window-system --quiet tests/run_tests.m
); then ok "test"; else bad "test"; fi

if (
set -e
if curl -fsS --max-time 2 http://127.0.0.1:5450/health >/dev/null 2>&1; then
  echo "port 5450 is already answering - stop that process before running this step"
  exit 1
fi
PORT=5450 ./bin/{{ npm_name }} > .octave-http.log 2>&1 &
server=$!
trap 'kill -TERM $server 2>/dev/null || true; for _ in $(seq 1 20); do kill -0 $server 2>/dev/null || break; sleep 0.1; done; kill -KILL $server 2>/dev/null || true; wait $server 2>/dev/null || true' EXIT
ready=1
for _ in $(seq 1 160); do
  if curl --max-time 2 -fsS http://127.0.0.1:5450/health >/dev/null 2>&1; then ready=0; break; fi
  sleep 0.25
done
if [ "$ready" -ne 0 ]; then cat .octave-http.log; echo "the server did not answer in time"; exit 1; fi
kill -0 $server 2>/dev/null || { cat .octave-http.log; echo "the server exited"; exit 1; }

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

check health '{"status":"ok"}' "$(curl --max-time 10 -fsS http://127.0.0.1:5450/health)"
check get '{"text":"hello world\n","lines":1,"words":2,"bytes":12}' \
  "$(curl --max-time 10 -fsS 'http://127.0.0.1:5450/stats?text=hello%20world%0A')"
check utf8 '{"text":"héllo wörld\n","lines":1,"words":2,"bytes":14}' \
  "$(curl --max-time 10 -fsS 'http://127.0.0.1:5450/stats?text=h%C3%A9llo%20w%C3%B6rld%0A')"
check post '{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}' \
  "$(curl --max-time 10 -fsS -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5450/stats)"
check escape '{"text":"café","lines":0,"words":1,"bytes":5}' \
  "$(curl --max-time 10 -fsS -X POST -H 'content-type: application/json' --data-binary '{"text":"caf\u00e9"}' http://127.0.0.1:5450/stats)"
check empty '{"text":"","lines":0,"words":0,"bytes":0}' \
  "$(curl --max-time 10 -fsS 'http://127.0.0.1:5450/stats?text=')"

status() { curl --max-time 10 -s -o /dev/null -w '%{http_code}' "$@"; }
check missing_text 422 "$(status -X POST -H 'content-type: application/json' --data-binary '{}' http://127.0.0.1:5450/stats)"
check non_string 422 "$(status -X POST -H 'content-type: application/json' --data-binary '{"text":42}' http://127.0.0.1:5450/stats)"
check invalid_json 422 "$(status -X POST -H 'content-type: application/json' --data-binary 'nope' http://127.0.0.1:5450/stats)"
check unknown_route 404 "$(status http://127.0.0.1:5450/nope)"
check wrong_method 405 "$(status -X DELETE http://127.0.0.1:5450/health)"
check not_found_detail '{"error":"not_found","detail":"no route for GET /nope"}' \
  "$(curl --max-time 10 -sS http://127.0.0.1:5450/nope)"

echo "all contract checks passed"

); then ok "http"; else bad "http"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

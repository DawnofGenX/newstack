#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v gleam >/dev/null 2>&1; then
  case "gleam" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: gleam is missing (install gleam)"; exit 1 ;;
  esac
fi
if ! command -v rebar3 >/dev/null 2>&1; then
  case "rebar3" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: rebar3 is missing (install rebar3)"; exit 1 ;;
  esac
fi
if ! command -v curl >/dev/null 2>&1; then
  case "curl" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: curl is missing (install curl)"; exit 1 ;;
  esac
fi

echo "smoke: gleam-mist-api"

if (
gleam deps download
); then ok "deps"; else bad "deps"; fi

if (
gleam format --check src test
); then ok "format"; else bad "format"; fi

if (
gleam test
); then ok "test"; else bad "test"; fi

if (
set -e
if curl -fsS --max-time 2 http://127.0.0.1:5416/health >/dev/null 2>&1; then echo 'port 5416 is already answering - stop that process before running this step'; exit 1; fi; setsid env PORT=5416 gleam run > .gleam.log 2>&1 &
server=$!
trap 'kill -TERM -"$server" 2>/dev/null || kill $server 2>/dev/null || true; wait $server 2>/dev/null || true' EXIT
ready=1
for _ in $(seq 1 240); do
  if curl -fsS --max-time 2 http://127.0.0.1:5416/health >/dev/null 2>&1; then ready=0; break; fi
  sleep 0.5
done
kill -0 $server 2>/dev/null || { cat .gleam.log; echo "the server exited before it answered"; exit 1; }
if [ "$ready" != 0 ]; then
  cat .gleam.log
  kill -TERM -"$server" 2>/dev/null || kill $server 2>/dev/null || true
  wait $server 2>/dev/null || true
  exit 1
fi
health=$(curl -fsS --max-time 10 http://127.0.0.1:5416/health)
stats=$(curl -fsS --max-time 10 'http://127.0.0.1:5416/stats?text=hello%20world%0A')
posted=$(curl -fsS --max-time 10 -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5416/stats)
missing=$(curl -s -o /dev/null --max-time 10 -w '%{http_code}' http://127.0.0.1:5416/stats)
broken=$(curl -s -o /dev/null --max-time 10 -w '%{http_code}' -X POST -H 'content-type: application/json' --data-binary 'nope' http://127.0.0.1:5416/stats)
gone=$(curl -s -o /dev/null --max-time 10 -w '%{http_code}' http://127.0.0.1:5416/nope)
kill -TERM -"$server" 2>/dev/null || kill $server 2>/dev/null || true
wait $server 2>/dev/null || true
test "$health" = '{"status":"ok"}' || { echo "health: $health"; exit 1; }
printf '%s' "$stats" | grep -q '"lines":1' || { echo "stats: $stats"; exit 1; }
printf '%s' "$stats" | grep -q '"bytes":12' || { echo "stats: $stats"; exit 1; }
printf '%s' "$posted" | grep -q '"words":3' || { echo "posted: $posted"; exit 1; }
test "$missing" = 422 || { echo "missing: $missing"; exit 1; }
test "$broken" = 422 || { echo "broken: $broken"; exit 1; }
test "$gone" = 404 || { echo "gone: $gone"; exit 1; }
echo "the service answered every check"

); then ok "http"; else bad "http"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

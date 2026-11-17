#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v guile >/dev/null 2>&1; then
  case "guile" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: guile is missing (install guile)"; exit 1 ;;
  esac
fi
if ! command -v guile-json >/dev/null 2>&1; then
  :
fi
if ! command -v curl >/dev/null 2>&1; then
  case "curl" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: curl is missing (install curl)"; exit 1 ;;
  esac
fi

echo "smoke: guile-http-api"

if (
guile -c '(use-modules (json)) (display "guile-json is installed") (newline)'
); then ok "install"; else bad "install"; fi

if (
env GUILE_AUTO_COMPILE=0 guile --no-auto-compile -L lib -L tests -s tests/run-tests.scm
); then ok "test"; else bad "test"; fi

if (
set -e
if curl -fsS --max-time 2 http://127.0.0.1:5431/health >/dev/null 2>&1; then echo 'port 5431 is already answering - stop that process before running this step'; exit 1; fi
PORT=5431 env GUILE_AUTO_COMPILE=0 guile --no-auto-compile -L lib main.scm > .guile.log 2>&1 &
server=$!
trap 'kill -TERM -"$server" 2>/dev/null || kill $server 2>/dev/null || true; wait $server 2>/dev/null || true' EXIT
ok=0
for _ in $(seq 1 120); do
  if curl -fsS --max-time 2 http://127.0.0.1:5431/health >/dev/null 2>&1; then ok=1; break; fi
  sleep 0.5
done
if [ $ok -ne 1 ]; then echo 'the service never answered'; cat .guile.log; kill $server 2>/dev/null || true; exit 1; fi
kill -0 $server 2>/dev/null || { cat .guile.log; echo 'the service exited before it answered'; exit 1; }
health=$(curl -sS --max-time 10 http://127.0.0.1:5431/health)
test "$health" = '{"status":"ok"}'
get=$(curl -sS --max-time 10 'http://127.0.0.1:5431/stats?text=hello%20world%0A')
printf '%s' "$get" | grep -q '"lines":1'
printf '%s' "$get" | grep -q '"bytes":12'
printf '%s' "$get" | grep -q '"words":2'
posted=$(curl -sS --max-time 10 -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5431/stats)
printf '%s' "$posted" | grep -q '"lines":2'
printf '%s' "$posted" | grep -q '"words":3'
missing=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:5431/stats)
test "$missing" = 422
broken=$(curl -sS --max-time 10 -H 'content-type: application/json' --data-binary 'nope' http://127.0.0.1:5431/stats)
printf '%s' "$broken" | grep -q 'invalid_json'
gone=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' http://127.0.0.1:5431/nope)
test "$gone" = 404
wrong=$(curl -sS --max-time 10 -o /dev/null -w '%{http_code}' -X DELETE http://127.0.0.1:5431/health)
test "$wrong" = 405
kill $server 2>/dev/null || true
wait $server 2>/dev/null || true
); then ok "http"; else bad "http"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

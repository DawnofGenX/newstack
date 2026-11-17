#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v crystal >/dev/null 2>&1; then
  case "crystal" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: crystal is missing (install crystal)"; exit 1 ;;
  esac
fi
if ! command -v shards >/dev/null 2>&1; then
  case "shards" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: shards is missing (install shards)"; exit 1 ;;
  esac
fi
if ! command -v curl >/dev/null 2>&1; then
  case "curl" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: curl is missing (install curl)"; exit 1 ;;
  esac
fi

echo "smoke: crystal-kemal-api"

if (
shards install
); then ok "install"; else bad "install"; fi

if (
crystal spec
); then ok "test"; else bad "test"; fi

if (
crystal tool format --check src spec
); then ok "format"; else bad "format"; fi

if (
shards build --release
); then ok "build"; else bad "build"; fi

if (
if curl -sS --max-time 2 http://127.0.0.1:5418/health >/dev/null 2>&1; then echo 'port 5418 is already answering - stop that process before running this step'; exit 1; fi; PORT=5418 ./bin/{{ npm_name }} >.kemal.log 2>&1 & srv=$!; ready=1; for _ in $(seq 1 120); do if curl --max-time 2 -sS http://127.0.0.1:5418/health >/dev/null 2>&1; then ready=0; break; fi; sleep 0.5; done; kill -0 $srv 2>/dev/null || { echo 'the server exited before it answered'; exit 1; }; if [ $ready -ne 0 ]; then cat .kemal.log; kill $srv 2>/dev/null; exit 1; fi; health=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5418/health); stats=$(curl --max-time 10 -s 'http://127.0.0.1:5418/stats?text=hello%20world%0A'); posted=$(curl --max-time 10 -s -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5418/stats); bad=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5418/stats); missing=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5418/nope); kill $srv 2>/dev/null; wait $srv 2>/dev/null || true; cat .kemal.log; test "$health" = 200 && printf '%s' "$stats" | grep -q '"lines":1' && printf '%s' "$stats" | grep -q '"bytes":12' && printf '%s' "$posted" | grep -q '"words":3' && test "$bad" = 422 && test "$missing" = 404
); then ok "http"; else bad "http"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

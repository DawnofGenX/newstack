#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v julia >/dev/null 2>&1; then
  case "julia" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: julia is missing (install julia)"; exit 1 ;;
  esac
fi
if ! command -v curl >/dev/null 2>&1; then
  case "curl" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: curl is missing (install curl)"; exit 1 ;;
  esac
fi

echo "smoke: julia-api"

if (
julia --project=. -e 'using Pkg; Pkg.instantiate(); Pkg.precompile()'
); then ok "instantiate"; else bad "instantiate"; fi

if (
julia --project=. test/runtests.jl
); then ok "test"; else bad "test"; fi

if (
julia --project=. --depwarn=error -e 'using TextstatApi'
); then ok "load"; else bad "load"; fi

if (
if curl -sS --max-time 2 http://127.0.0.1:5422/health >/dev/null 2>&1; then echo 'port 5422 is already serving something else - stop it before running this step'; exit 1; fi; PORT=5422 julia --project=. src/main.jl > .julia.log 2>&1 & server=$!; ready=1; for _ in $(seq 1 240); do if curl -sS --max-time 2 http://127.0.0.1:5422/health >/dev/null 2>&1; then ready=0; break; fi; sleep 0.5; done; if [ "$ready" != 0 ]; then cat .julia.log; echo 'the server did not answer'; kill $server 2>/dev/null || true; wait $server 2>/dev/null || true; exit 1; fi; kill -0 $server 2>/dev/null || { cat .julia.log; echo 'the server exited before it answered'; exit 1; }; health=$(curl -sS --max-time 10 http://127.0.0.1:5422/health); got=$(curl -sS --max-time 10 'http://127.0.0.1:5422/stats?text=hello%20world%0A'); posted=$(curl -sS --max-time 10 -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5422/stats); missing=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 http://127.0.0.1:5422/stats); broken=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 -X POST -H 'content-type: application/json' --data-binary '{not json' http://127.0.0.1:5422/stats); gone=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 http://127.0.0.1:5422/nope); kill $server 2>/dev/null || true; wait $server 2>/dev/null || true; test "$health" = '{"status":"ok"}'; echo "$got" | grep -q '"lines":1'; echo "$got" | grep -q '"bytes":12'; echo "$posted" | grep -q '"words":3'; test "$missing" = 422; test "$broken" = 422; test "$gone" = 404
); then ok "http"; else bad "http"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

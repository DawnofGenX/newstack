#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v dart >/dev/null 2>&1; then
  case "dart" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: dart is missing (install dart)"; exit 1 ;;
  esac
fi
if ! command -v curl >/dev/null 2>&1; then
  case "curl" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: curl is missing (install curl)"; exit 1 ;;
  esac
fi

echo "smoke: dart-shelf-api"

if (
dart pub get
); then ok "get"; else bad "get"; fi

if (
dart analyze --fatal-infos
); then ok "analyze"; else bad "analyze"; fi

if (
dart test
); then ok "test"; else bad "test"; fi

if (
if curl -fsS --max-time 2 http://127.0.0.1:5411/health >/dev/null 2>&1; then echo 'port 5411 is already answering - stop that process before running this step'; exit 1; fi; PORT=5411 dart run bin/{{ npm_name }}.dart >.dart.log 2>&1 & srv=$!; ready=1; for _ in $(seq 1 60); do if curl --max-time 2 -fsS http://127.0.0.1:5411/health >/dev/null 2>&1; then ready=0; break; fi; sleep 0.5; done; kill -0 $srv 2>/dev/null || { echo 'the server exited before it answered'; exit 1; }; if [ $ready -ne 0 ]; then cat .dart.log; kill $srv 2>/dev/null; exit 1; fi; health=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5411/health); stats=$(curl --max-time 10 -s 'http://127.0.0.1:5411/stats?text=hello%20world%0A'); posted=$(curl --max-time 10 -s -X POST -H 'content-type: application/json' --data-binary '{"text":"a b\nc\n"}' http://127.0.0.1:5411/stats); bad=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5411/stats); nonjson=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' -X POST --data-binary 'nope' http://127.0.0.1:5411/stats); missing=$(curl --max-time 10 -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5411/nope); kill $srv 2>/dev/null; wait $srv 2>/dev/null; cat .dart.log; test "$health" = 200 && printf '%s' "$stats" | grep -q '"lines":1' && printf '%s' "$stats" | grep -q '"bytes":12' && printf '%s' "$posted" | grep -q '"words":3' && test "$bad" = 422 && test "$nonjson" = 422 && test "$missing" = 404
); then ok "http"; else bad "http"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

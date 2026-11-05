#!/usr/bin/env bash
# Contract smoke test. Builds first when there is no build yet, so the script is
# runnable on a fresh clone as well as after `npm run build`.
set -euo pipefail
PORT="${PORT:-5465}"
LOG=$(mktemp)
server_pid=""
cleanup() {
  if [ -n "$server_pid" ]; then kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; fi
  rm -f "$LOG"
}
trap cleanup EXIT

[ -f .output/server/index.mjs ] || npm run build

if command -v ss >/dev/null && ss -ltn 2>/dev/null | grep -q ":$PORT "; then
  echo "smoke: port $PORT is already in use" >&2
  exit 1
fi

PORT="$PORT" node .output/server/index.mjs >"$LOG" 2>&1 &
server_pid=$!

for _ in $(seq 1 50); do
  if curl -fsS -o /dev/null "http://127.0.0.1:$PORT/api/stats?text=x" 2>/dev/null; then break; fi
  if ! kill -0 "$server_pid" 2>/dev/null; then echo "smoke: server exited" >&2; cat "$LOG" >&2; exit 1; fi
  sleep 0.2
done

fail=0
check() { # name expected actual
  if [ "$2" = "$3" ]; then printf 'ok   %s\n' "$1"; else printf 'FAIL %s (want %s, got %s)\n' "$1" "$2" "$3"; fail=1; fi
}

check health "200" "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/api/stats?text=x")"
check ssr-body "200" "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/")"
check ssr-rendered "yes" "$(curl -s "http://127.0.0.1:$PORT/" | grep -q 'data-app="stats"' && echo yes || echo no)"
check stats-utf8 '{"text":"héllo wörld\n","lines":1,"words":2,"bytes":14}' \
  "$(curl -s "http://127.0.0.1:$PORT/api/stats?text=h%C3%A9llo%20w%C3%B6rld%0A")"
check missing-text "422" "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/api/stats")"
check missing-body "missing_text" "$(curl -s "http://127.0.0.1:$PORT/api/stats" | python3 -c 'import json,sys; print(json.load(sys.stdin)["error"])')"
check wrong-method "405" "$(curl -s -o /dev/null -w '%{http_code}' -X POST "http://127.0.0.1:$PORT/api/stats")"
check unknown-route "404" "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/no-such-page")"

if [ "$fail" -ne 0 ]; then echo "smoke: FAILED" >&2; exit 1; fi
echo "smoke: all checks passed"

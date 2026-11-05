#!/usr/bin/env bash
# Live check: build the bundle, serve it, assert the page, its assets and the 404 rule.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
PORT=${PORT:-5461}
BASE="http://127.0.0.1:${PORT}"
BROWSER_DIR="$ROOT/dist/{{ npm_name }}/browser"
LOG="$ROOT/.angular-http.log"

if curl -fsS --max-time 2 "${BASE}/" >/dev/null 2>&1; then
  echo "port ${PORT} is already answering - stop that process before running this step" >&2
  exit 1
fi

fail() { echo "FAIL $1" >&2; exit 1; }

[ -f "$BROWSER_DIR/index.html" ] || (cd "$ROOT" && npx ng build)

PORT=$PORT node "$ROOT/tools/serve.mjs" "$BROWSER_DIR" >"$LOG" 2>&1 &
server=$!
trap 'kill -TERM -"$server" 2>/dev/null || kill -TERM "$server" 2>/dev/null || true; wait "$server" 2>/dev/null || true' EXIT

for _ in $(seq 1 160); do
  kill -0 "$server" 2>/dev/null || { cat "$LOG" >&2; fail "server exited before it answered"; }
  curl -fsS --max-time 2 "${BASE}/" >/dev/null 2>&1 && break
  sleep 0.25
done
curl -fsS --max-time 2 "${BASE}/" >/dev/null || { cat "$LOG" >&2; fail "server never answered"; }

index=$(curl -fsS --max-time 2 "${BASE}/")
case "$index" in *"<app-root"*) echo "ok index" ;; *) fail "index.html does not contain app-root" ;; esac

# Take the first match with parameter expansion: a `| head -1` here would
# be killed by SIGPIPE under `set -o pipefail` whenever sed writes twice.
bundle=$(printf '%s' "$index" | sed -n 's/.*src="\([^"]*\.js\)".*/\1/p')
bundle=${bundle%%$'\n'*}
[ -n "$bundle" ] || fail "index.html has no script bundle"
# `ng build` emits a relative script src, so it needs the leading slash for curl.
case "$bundle" in /*) ;; *) bundle="/$bundle" ;; esac
script=$(curl -fsS --max-time 5 "${BASE}${bundle}")
case "$script" in *"Text stats"*) echo "ok bundle ($bundle)" ;; *) fail "bundle $bundle does not contain the page title" ;; esac

fallback=$(curl -fsS --max-time 2 "${BASE}/some/client/route")
case "$fallback" in *"<app-root"*) echo "ok spa fallback" ;; *) fail "unknown route did not fall back to index.html" ;; esac

code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 2 "${BASE}/missing.js")
[ "$code" = "404" ] || fail "missing.js answered $code, wanted 404"
echo "ok missing asset 404"

echo "smoke: all checks passed"

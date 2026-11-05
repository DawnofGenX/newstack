#!/usr/bin/env bash
# Smoke test: build the project, run it for real, and check the numbers it prints.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"

NODE="${NODE:-node}"
NPM="${NPM:-npm}"
PROGRAM="$("$NODE" -p 'require("./package.json").name')"
PORT="${PORT:-5480}"
work="$(mktemp -d)"
server_pid=""
cleanup() {
  if [ -n "$server_pid" ]; then kill "$server_pid" 2>/dev/null || true; fi
  rm -rf "$work"
}
trap cleanup EXIT

passed=0
failed=0
ok() { passed=$((passed + 1)); printf '  ok    %s\n' "$1"; }
bad() { failed=$((failed + 1)); printf '  FAIL  %s\n        %s\n' "$1" "$2"; }
check_equal() {
  if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "wanted $3, got $2"; fi
}
check_contains() {
  if printf '%s' "$2" | grep -qF -- "$3"; then ok "$1"; else bad "$1" "wanted to see: $3"; fi
}
run() { "$NODE" dist/src/main.js "$@"; }

if [ ! -d node_modules ]; then
  "$NPM" install --no-audit --no-fund >"$work/install.log" 2>&1 || { bad "npm install" "$(tail -3 "$work/install.log")"; exit 1; }
fi

"$NPM" run build >"$work/build.log" 2>&1
check_equal "the build succeeds" "$?" "0"
if [ ! -f dist/src/main.js ]; then bad "dist/src/main.js exists" "no build output"; exit 1; fi
ok "dist/src/main.js exists"

out="$(run --version 2>&1)"
check_equal "--version exits 0" "$?" "0"
check_contains "--version names the program" "$out" "$PROGRAM 0.1.0"

out="$(run help 2>&1)"
check_contains "help lists demo" "$out" "demo"
check_contains "help lists check" "$out" "check"
check_contains "help lists selftest" "$out" "selftest"

out="$(run demo 2>&1)"
check_equal "demo exits 0" "$?" "0"
check_contains "demo shows the empty 304" "$out" "1. a 304 carries no body"
check_contains "demo measures zero body bytes" "$out" "304, 0 byte(s) of body"
check_contains "demo names the weak comparison" "$out" "weak comparison ignores W/"
check_contains "demo shows the refused write" "$out" "412"
check_contains "demo shows the date losing" "$out" "3. If-None-Match wins over If-Modified-Since"
check_contains "demo shows the vary mistake" "$out" "wrong representation"
check_contains "demo keeps the stored body" "$out" "5. a 304 refreshes freshness"
check_contains "demo shows the empty entry" "$out" "the entry is now empty and still fresh"
check_equal "demo keeps six stories" "$(printf '%s' "$out" | grep -c 'kept        yes')" "6"

out="$(run selftest 2>&1)"
check_equal "selftest exits 0" "$?" "0"
check_contains "selftest reports its checks" "$out" "checks passed"

"$NODE" --test dist/tests/*.test.js >"$work/test.log" 2>&1
check_equal "the unit tests pass" "$?" "0"

run --rounds 0 >"$work/bad.log" 2>&1
check_equal "a bad round count exits 2" "$?" "2"
run nope >"$work/unknown.log" 2>&1
check_equal "an unknown command exits 2" "$?" "2"
run check >"$work/nourl.log" 2>&1
check_equal "check without a url exits 2" "$?" "2"

"$NODE" dist/src/main.js serve --port "$PORT" >"$work/serve.log" 2>&1 &
server_pid=$!
ready=""
for _ in $(seq 1 60); do
  if curl -fsS -o /dev/null "http://127.0.0.1:$PORT/profile" 2>/dev/null; then ready=yes; break; fi
  sleep 0.1
done
if [ "$ready" = "yes" ]; then
  ok "the server answers on port $PORT"
  headers="$(curl -sS -D - -o "$work/body1" "http://127.0.0.1:$PORT/profile")"
  check_equal "a plain request answers 200" "$(printf '%s' "$headers" | head -1 | tr -d '\r' | cut -d' ' -f2)" "200"
  tag="$(printf '%s' "$headers" | tr -d '\r' | awk 'tolower($1)=="etag:"{print $2}')"
  check_contains "the response carries a tag" "$tag" '"'
  size1="$(wc -c <"$work/body1")"
  check_contains "the plain body has content" "$(cat "$work/body1")" "ada"
  read -r code size2 < <(curl -sS -o "$work/body2" -w '%{http_code} %{size_download}' -H "If-None-Match: $tag" "http://127.0.0.1:$PORT/profile")
  check_equal "a matching tag answers 304" "$code" "304"
  check_equal "the 304 body is empty" "$size2" "0"
  check_equal "the 304 saved the body bytes" "$size1" "$size1"
  code="$(curl -sS -o /dev/null -w '%{http_code}' -X PUT -H "If-Match: W/$tag" "http://127.0.0.1:$PORT/profile")"
  check_equal "a weak If-Match answers 412" "$code" "412"
  code="$(curl -sS -o /dev/null -w '%{http_code}' -X PUT "http://127.0.0.1:$PORT/profile")"
  check_equal "an unconditional write answers 428" "$code" "428"
  plain="$(curl -sS -H 'Accept: text/plain' "http://127.0.0.1:$PORT/report")"
  check_contains "the plain representation differs" "$plain" "v1"
  jsonfirst="$(curl -sS -H 'Accept: application/json' "http://127.0.0.1:$PORT/report" | head -c 1)"
  check_equal "the json representation is an object" "$jsonfirst" "{"
else
  bad "the server answers on port $PORT" "$(tail -3 "$work/serve.log")"
fi
kill "$server_pid" 2>/dev/null || true
server_pid=""

printf '\nsmoke: %d passed, %d failed\n' "$passed" "$failed"
[ "$failed" -eq 0 ]

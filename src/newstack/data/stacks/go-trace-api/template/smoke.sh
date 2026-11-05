#!/usr/bin/env bash
# Contract over a real socket for the tracing text-stats service.
set -euo pipefail

PORT="${PORT:-5475}"
BASE="http://127.0.0.1:$PORT"
HERE="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
server=""

cleanup() {
  if [ -n "$server" ]; then
    kill -TERM "$server" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "$server" 2>/dev/null || break
      sleep 0.1
    done
    kill -KILL "$server" 2>/dev/null || true
    wait "$server" 2>/dev/null || true
  fi
  rm -rf "$work"
}
trap cleanup EXIT

if curl -fsS --max-time 1 "$BASE/health" >/dev/null 2>&1; then
  echo "FAIL: port $PORT is already answering - stop that process before running this step" >&2
  exit 1
fi

if [ ! -x "$HERE/build/{{ npm_name }}" ]; then
  (cd "$HERE" && go build -o build/{{ npm_name }} .)
fi

PORT="$PORT" "$HERE/build/{{ npm_name }}" >"$work/server.log" 2>&1 &
server=$!

ready=0
for _ in $(seq 1 160); do
  if curl -fsS --max-time 1 "$BASE/health" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 0.25
done
if [ "$ready" -ne 1 ]; then
  echo "FAIL: the service never answered on $PORT" >&2
  cat "$work/server.log" >&2
  exit 1
fi
kill -0 "$server"

failures=0
check() {
  local name="$1" needle="$2" haystack="$3"
  if printf '%s' "$haystack" | grep -Fiq -- "$needle"; then
    echo "ok   $name"
  else
    echo "FAIL $name: wanted [$needle] in [$haystack]"
    failures=$((failures + 1))
  fi
}
code() { curl -sS --max-time 10 -o "$work/body" -w '%{http_code}' "$@"; }
body() { cat "$work/body"; }

status=$(code "$BASE/health")
check "health status" "200" "$status"
check "health body" '"status":"ok"' "$(body)"

status=$(code "$BASE/stats?text=h%C3%A9llo+w%C3%B6rld%0A")
check "utf8 status" "200" "$status"
check "utf8 counts" '"lines":1,"words":2,"bytes":14' "$(body)"

status=$(code -D "$work/head" "$BASE/stats?text=hi")
check "a traceparent is announced" "traceparent: 00-" "$(cat "$work/head")"
check "a trace id is announced" "X-Trace-Id:" "$(cat "$work/head")"
served_span=$(grep -i '^x-span-id:' "$work/head" | tr -d '\r' | awk '{print $2}')
check "the served span is announced" "16" "${#served_span}"
check "stats wire order" '{"text":"hi","lines":0,"words":1,"bytes":2}' "$(body)"

trace="4bf92f3577b34da6a3ce929d0e0e4736"
parent_span="00f067aa0ba902b7"
status=$(code -H "traceparent: 00-$trace-$parent_span-01" "$BASE/stats?text=one+two")
check "a supplied trace is accepted" "200" "$status"
child_span=$(grep -i '^x-span-id:' "$work/head" 2>/dev/null | tr -d '\r' | awk '{print $2}' || true)

status=$(code "$BASE/spans?trace=$trace")
check "the span export answers" "200" "$status"
check "the caller's span is the parent" "\"parent_span_id\":\"$parent_span\"" "$(body)"
check "the child span is exported" '"name":"count"' "$(body)"
check "the trace is the caller's" "\"trace_id\":\"$trace\"" "$(body)"
check "a duration is recorded" '"duration_ms":' "$(body)"

status=$(code -H "traceparent: 00-$trace-$parent_span-00" "$BASE/stats?text=two")
check "an unsampled trace is accepted" "200" "$status"
check "an unsampled response still counts" '"text":"two","lines":0,"words":1,"bytes":3' "$(body)"
code "$BASE/spans?trace=$trace" >/dev/null
stored=$(printf '%s' "$(body)" | grep -o '"name":"stats"' | wc -l | tr -d ' ')
check "unsampled work is not exported" "1" "$stored"

status=$(code -H "traceparent: 00-xyz" "$BASE/stats?text=bad")
check "a malformed traceparent is refused" "400" "$status"
check "it is named" '"error":"invalid_traceparent"' "$(body)"

status=$(code -X POST -d '{}' "$BASE/stats")
check "missing text is 422" "422" "$status"
check "missing text is named" '"error":"missing_text"' "$(body)"

status=$(code -X POST -d '{"text":42}' "$BASE/stats")
check "a non-string text is 422" "422" "$status"

status=$(code -X POST -d 'oops' "$BASE/stats")
check "broken json is 422" "422" "$status"
check "broken json is named" '"error":"invalid_json"' "$(body)"

head -c 70000 /dev/zero | tr '\0' 'x' > "$work/huge"
status=$(code -X POST --data-binary "@$work/huge" "$BASE/stats")
check "a huge body is 413" "413" "$status"

status=$(code "$BASE/stats?text=")
check "empty text is zero" '"lines":0,"words":0,"bytes":0' "$(body)"

status=$(code "$BASE/nope")
check "unknown path is 404" "404" "$status"
check "404 names the route" "no route for GET /nope" "$(body)"

status=$(code -X PUT "$BASE/health")
check "wrong method is 405" "405" "$status"
check "405 is named" '"error":"method_not_allowed"' "$(body)"

status=$(code "$BASE/spans?trace=zzz")
check "a bad trace filter is 400" "400" "$status"

if [ "$failures" -ne 0 ]; then
  echo "smoke: $failures check(s) failed"
  exit 1
fi
echo "smoke: all checks passed"

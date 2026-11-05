#!/usr/bin/env bash
# smoke.sh — the contract over a real socket, plus a scrape validated the way a
# Prometheus server would validate it.
set -euo pipefail

PORT="${PORT:-5474}"
HOST="${HOST:-127.0.0.1}"
BASE="http://$HOST:$PORT"
LOG="$(pwd)/.metrics-http.log"
failures=0

check() { # check <label> <expected> <actual>
  if [ "$2" = "$3" ]; then
    printf 'ok   %s\n' "$1"
  else
    printf 'FAIL %s\n  expected: %s\n  actual:   %s\n' "$1" "$2" "$3"
    failures=$((failures + 1))
  fi
}

contains() { # contains <label> <needle> <haystack>
  case "$3" in
    *"$2"*) printf 'ok   %s\n' "$1" ;;
    *) printf 'FAIL %s\n  wanted substring: %s\n  in: %s\n' "$1" "$2" "$3"
       failures=$((failures + 1)) ;;
  esac
}

body() { # body <method> <path> [data] -> prints "<status> <body>"
  if [ "$1" = "GET" ]; then
    curl -sS -o /tmp/metrics-smoke.body -w '%{http_code}' "$BASE$2"
  else
    curl -sS -o /tmp/metrics-smoke.body -w '%{http_code}' -X "$1" --data-binary "$3" "$BASE$2"
  fi
  printf ' '
  cat /tmp/metrics-smoke.body
}

status_of() { printf '%s' "${1%% *}"; }
payload_of() { printf '%s' "${1#* }"; }

# A stale listener on the port would answer for us and make every check meaningless.
if curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1; then
  echo "FAIL port $PORT is already answering - stop that process before running this step" >&2
  exit 1
fi

node src/main.js >"$LOG" 2>&1 &
server=$!
trap 'kill -TERM -"$server" 2>/dev/null || kill -TERM "$server" 2>/dev/null || true
      for _ in $(seq 1 20); do kill -0 "$server" 2>/dev/null || break; sleep 0.1; done
      kill -KILL "$server" 2>/dev/null || true
      wait "$server" 2>/dev/null || true
      rm -f /tmp/metrics-smoke.body' EXIT

for _ in $(seq 1 160); do
  curl -fsS --max-time 2 "$BASE/health" >/dev/null 2>&1 && break
  sleep 0.25
done
kill -0 "$server" 2>/dev/null || { echo "server died:"; cat "$LOG"; exit 1; }

check "health" '200 {"status":"ok"}' "$(body GET /health)"

get_ascii="$(body GET '/stats?text=a%20b%0Ac')"
check "GET /stats ascii" '200 {"text":"a b\nc","lines":1,"words":3,"bytes":5}' "$get_ascii"

get_utf8="$(body GET '/stats?text=h%C3%A9llo%20w%C3%B6rld%0A')"
check "GET /stats utf8" '200 {"text":"héllo wörld\n","lines":1,"words":2,"bytes":14}' "$get_utf8"

post="$(body POST /stats '{"text":"a b\nc\n"}')"
check "POST /stats" '200 {"text":"a b\nc\n","lines":2,"words":3,"bytes":6}' "$post"

for case in '{}|missing_text' '{oops|invalid_json' '[1,2,3]|invalid_body' '{"text":42}|invalid_text'; do
  data="${case%%|*}"
  code="${case##*|}"
  answer="$(body POST /stats "$data")"
  check "POST $data is 422 $code" "422 {\"error\":\"$code\"}" "$answer"
done

big="$(node -e 'process.stdout.write(JSON.stringify({text: "x".repeat(70000)}))')"
answer="$(body POST /stats "$big")"
check "an oversized body is 413" '413 {"error":"body_too_large"}' "$answer"

check "unknown route 404" '404 {"error":"not_found","detail":"no route for GET /nope"}' "$(body GET /nope)"
check "wrong method 405" '405 {"error":"method_not_allowed"}' "$(body POST /health '{}')"

check "event 1" '200 {"id":"1","kind":"viewed"}' "$(body GET /events/1)"
check "event 2" '200 {"id":"2","kind":"viewed"}' "$(body GET /events/2)"

ctype="$(curl -sS -o /tmp/metrics-scrape.txt -w '%{content_type}' "$BASE/metrics")"
check "metrics content type" 'text/plain; version=0.0.4; charset=utf-8' "$ctype"

# Validate the BODY AS A FILE: `$(...)` strips the trailing newline, and a payload
# without one is invalid exposition — validating a command substitution would test a
# body no scraper ever receives.
if node tools/check_scrape.mjs < /tmp/metrics-scrape.txt >/tmp/metrics-scrape.out 2>&1; then
  printf 'ok   scrape is valid exposition (%s)\n' "$(head -1 /tmp/metrics-scrape.out)"
else
  printf 'FAIL scrape is invalid\n'
  cat /tmp/metrics-scrape.out
  failures=$((failures + 1))
fi

contains "textstat_up is 1" 'textstat_up 1' "$(cat /tmp/metrics-scrape.txt)"
contains "the events gauge saw two ids" 'textstat_events_seen 2' "$(cat /tmp/metrics-scrape.txt)"
collapsed="$(grep -c 'textstat_requests_total{method="GET",route="/events/:id",status="200"}' /tmp/metrics-scrape.txt)"
check "two ids collapse into one route series" '1' "$collapsed"
contains "requests are labelled by status" 'textstat_requests_total{method="GET",route="/health",status="200"} 2' "$(cat /tmp/metrics-scrape.txt)"
contains "a duration histogram is exported" 'textstat_request_duration_seconds_bucket{le="+Inf",route="/stats"}' "$(cat /tmp/metrics-scrape.txt)"
inf="$(grep -c 'le="+Inf"' /tmp/metrics-scrape.txt)"
counts="$(grep -c '_count{' /tmp/metrics-scrape.txt)"
check "one +Inf bucket per histogram label set" "$counts" "$inf"
rm -f /tmp/metrics-scrape.txt /tmp/metrics-scrape.out

if [ "$failures" -ne 0 ]; then
  printf 'smoke: %d check(s) failed\n' "$failures" >&2
  cat "$LOG" >&2
  exit 1
fi
printf 'smoke: all checks passed\n'

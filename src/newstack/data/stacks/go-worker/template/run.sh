#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
bin="$work/blog-count"
go build -o "$bin" .

"$bin" --input jobs.ndjson --state "$work/seen.json" --backoff 1ms > "$work/first.ndjson" 2> "$work/first.err"
echo "--- first run"
cat "$work/first.ndjson"

test "$(wc -l < "$work/first.ndjson")" -eq 6
grep -q '"id":"one","status":"ok","attempts":1,"lines":2,"words":3,"bytes":6' "$work/first.ndjson"
grep -q '"id":"two","status":"ok","attempts":3' "$work/first.ndjson"
grep -q '"id":"three","status":"failed","attempts":3,"lines":0,"words":0,"bytes":0,"code":"transient"' "$work/first.ndjson"
grep -q '"id":"four","status":"ok","attempts":1,"lines":1,"words":2,"bytes":14' "$work/first.ndjson"
grep -q '"code":"unknown_op"' "$work/first.ndjson"
grep -q '"code":"missing_id"' "$work/first.ndjson"

echo "--- replay"
"$bin" --input jobs.ndjson --state "$work/seen.json" --backoff 1ms > "$work/second.ndjson" 2>/dev/null
cat "$work/second.ndjson"
test "$(grep -c '"status":"skipped"' "$work/second.ndjson")" -eq 3
grep -q '"id":"three","status":"failed","attempts":3' "$work/second.ndjson"

echo "--- drain"
fifo="$work/jobs.fifo"
mkfifo "$fifo"
"$bin" --state "$work/drain.json" --backoff 1ms < "$fifo" > "$work/drain.ndjson" 2> "$work/drain.err" &
worker=$!
exec 3> "$fifo"
printf '%s\n' '{"id":"slow","op":"count","text":"x y\n"}' >&3
sleep 0.5
kill -TERM "$worker"
set +e
wait "$worker"
status=$?
set -e
exec 3>&-
cat "$work/drain.ndjson"
test "$status" -eq 0
test "$(wc -l < "$work/drain.ndjson")" -eq 1
grep -q 'draining' "$work/drain.err"
echo "all worker checks passed"

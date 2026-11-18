#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-ndjson-split"

npm test

tmp=$(mktemp -d)
printf '{"id":1}\n{"id":2}\n{"id":3}\n{"id":4}\n{"id":5}\n' > "$tmp/data.ndjson"

node src/cli.js --file "$tmp/data.ndjson" --out-dir "$tmp/parts" --max-lines 2 > "$tmp/summary.json"
grep -q '"records": 5' "$tmp/summary.json"
grep -q '"chunks": 3' "$tmp/summary.json"

test -f "$tmp/parts/part-0001.ndjson"
test -f "$tmp/parts/part-0003.ndjson"
test "$(wc -l < "$tmp/parts/part-0003.ndjson")" -eq 1

rm -rf "$tmp"
echo "smoke: ok"

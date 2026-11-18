#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-csv-stats"

npm test

tmp=$(mktemp -d)
printf 'item,qty,note\na,2,x\nb,4,"y, z"\nc,,w\n' > "$tmp/data.csv"

node src/cli.js --file "$tmp/data.csv" > "$tmp/stats.json"
grep -q '"rows": 3' "$tmp/stats.json"
grep -q '"mean": 3' "$tmp/stats.json"
grep -q '"column": "qty"' "$tmp/stats.json"

node src/cli.js --file "$tmp/data.csv" --table | grep -q 'mean 3'

printf 'a,b\n1\n' > "$tmp/bad.csv"
if node src/cli.js --file "$tmp/bad.csv" > "$tmp/bad.out" 2>&1; then
  echo "expected ragged row failure"
  exit 1
fi
grep -q 'row 2 has 1 fields' "$tmp/bad.out"

rm -rf "$tmp"
echo "smoke: ok"

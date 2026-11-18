#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "smoke: kotlin-csv-report"

gradle test --quiet

tmp=$(mktemp)
printf 'name,dept,score\nalice,eng,10\nbob,eng,20\ncarol,sales,5\n' > "$tmp"
out=$(gradle run --quiet --args="$tmp --group=dept --sum=score" 2>&1)
echo "$out"
echo "$out" | grep -q "rows=3"
echo "$out" | grep -q "eng 2"
echo "$out" | grep -q "sum=35.0"

echo "smoke: PASS"
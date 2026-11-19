#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "smoke: kotlin-jsonpath-cli"

gradle test --quiet

tmp=$(mktemp)
printf '{"store":{"book":[{"author":"A"},{"author":"B"}]}}' > "$tmp"
out=$(gradle run --quiet --args="\$ --file $tmp" 2>&1)
echo "$out"
echo "$out" | grep -q '"store"'

tmp2=$(mktemp)
printf '{"a":[1,2,3]}' > "$tmp2"
out2=$(gradle run --quiet --args="$.a[*] --file $tmp2" 2>&1)
echo "$out2"
echo "$out2" | grep -q '1'
echo "$out2" | grep -q '3'

echo "smoke: PASS"

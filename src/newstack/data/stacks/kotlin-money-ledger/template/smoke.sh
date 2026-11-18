#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "smoke: kotlin-money-ledger"

gradle test --quiet

tmp=$(mktemp)
printf 'cash,100.00\ninventory,-40.00\ncash,-12.50\n' > "$tmp"
out=$(gradle run --quiet --args="$tmp" 2>&1)
echo "$out"
echo "$out" | grep -q "cash 87.50"
echo "$out" | grep -q "inventory -40.00"
echo "$out" | grep -q "total 47.50"

usage=$(gradle run --quiet 2>&1)
echo "$usage" | grep -q "usage: {{ npm_name }}"

echo "smoke: PASS"

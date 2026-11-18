#!/usr/bin/env bash
set -euo pipefail

echo "smoke: {{ npm_name }}"

npm test

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf 'alpha\nbeta\ngamma\n' > "$tmp/old.txt"
printf 'alpha\nBETA\ngamma\n' > "$tmp/new.txt"

out=$(node src/cli.js "$tmp/old.txt" "$tmp/new.txt")
echo "$out"
echo "$out" | grep -q "^--- $tmp/old.txt"
echo "$out" | grep -q "^-beta"
echo "$out" | grep -q "^+BETA"

cp "$tmp/old.txt" "$tmp/same.txt"
node src/cli.js "$tmp/old.txt" "$tmp/same.txt" | grep -q "identical"

echo "smoke: ok"

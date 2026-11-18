#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-zlib-stat-cli"

npm test

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

printf 'the quick brown fox jumps over the lazy dog\n' > "$tmp/in.txt"
node src/cli.js compress "$tmp/in.txt" --level 9 --out "$tmp/in.gz"
test -s "$tmp/in.gz"
node src/cli.js decompress "$tmp/in.gz" --out "$tmp/out.txt"
cmp "$tmp/in.txt" "$tmp/out.txt"
node src/cli.js stats "$tmp/in.gz" | grep -q '^input=[0-9]* bytes compressed='
node src/cli.js stats "$tmp/in.txt" | grep -q '^unknown bytes='
set +e
node src/cli.js compress --level 12 "$tmp/in.txt" > /dev/null 2>&1
code=$?
set -e
test "$code" -eq 2

echo "smoke: ok"

#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-sri-hash-cli"

npm test

tmp=$(mktemp -d)
printf 'hello' > "$tmp/a.txt"

sri=$(node src/cli.js hash "$tmp/a.txt" | cut -d' ' -f1)
case "$sri" in
  sha384-*) ;;
  *) echo "unexpected integrity: $sri"; exit 1 ;;
esac

node src/cli.js verify "$tmp/a.txt" "$sri" | grep -q '^ok$'

printf 'hello!' > "$tmp/a.txt"
if node src/cli.js verify "$tmp/a.txt" "$sri" > "$tmp/out" 2>&1; then
  echo "expected verification failure"
  exit 1
fi
grep -q '^fail$' "$tmp/out"

rm -rf "$tmp"
echo "smoke: ok"

#!/usr/bin/env bash
set -euo pipefail

echo "smoke: ruby-huffman-cli"

ruby -cw lib/huffman.rb >/dev/null
ruby -cw lib/huffman/cli.rb >/dev/null
rake test

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

printf 'abracadabra' > "$tmp/in.txt"
./bin/{{ npm_name }} encode "$tmp/in.txt" > "$tmp/payload.txt"
./bin/{{ npm_name }} decode "$tmp/payload.txt" > "$tmp/out.txt"
test "$(cat "$tmp/out.txt")" = "abracadabra"

./bin/{{ npm_name }} table "$tmp/in.txt" | grep -q '"a"'
./bin/{{ npm_name }} stats "$tmp/in.txt" | grep -qx 'symbols=5'
./bin/{{ npm_name }} --help | grep -q 'usage: '

if ./bin/{{ npm_name }} squash "$tmp/in.txt" >/dev/null 2>&1; then
  echo "smoke: an unknown command must exit 2" >&2
  exit 1
fi

echo "smoke: ok"

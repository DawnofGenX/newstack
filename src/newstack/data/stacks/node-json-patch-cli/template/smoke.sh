#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-json-patch-cli"

npm test

tmp=$(mktemp -d)
echo '{"foo":1}' > "$tmp/doc.json"
echo '[{"op":"add","path":"/bar","value":2}]' > "$tmp/patch.json"
node src/cli.js apply "$tmp/doc.json" "$tmp/patch.json" | grep -q '"bar": 2'

rm -rf "$tmp"
echo "smoke: ok"
#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-zod-config"

npm test

tmp=$(mktemp -d)
echo '{"port":4000,"host":"filehost"}' > "$tmp/c.json"
node src/cli.js --config "$tmp/c.json" --port 6000 --out "$tmp/out.json"
grep -q '"port": 6000' "$tmp/out.json"
grep -q '"host": "filehost"' "$tmp/out.json"

rm -rf "$tmp"
echo "smoke: ok"
#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-yaml-lite"

npm test

tmp=$(mktemp -d)
printf 'server:\n  host: localhost\n  port: 8080\ntags: [a, b]\n' > "$tmp/cfg.yaml"
node src/cli.js --json "$tmp/cfg.yaml" > "$tmp/out.json"
grep -q '"port": 8080' "$tmp/out.json"
grep -q '"tags": \[' "$tmp/out.json"
test "$(node src/cli.js --get server.host "$tmp/cfg.yaml")" = "localhost"

rm -rf "$tmp"
echo "smoke: ok"

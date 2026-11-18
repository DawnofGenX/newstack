#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-env-schema"

npm test

tmp=$(mktemp -d)
cat > "$tmp/app.env" <<'ENV'
# sample config
SERVICE_NAME=checkout
DATABASE_URL="https://db.example.com/app"
PORT=8080
DEBUG=yes
ENV

node src/cli.js --file "$tmp/app.env" > "$tmp/out.json"
grep -q '"PORT": 8080' "$tmp/out.json"
grep -q '"DEBUG": true' "$tmp/out.json"
grep -q '"SERVICE_NAME": "checkout"' "$tmp/out.json"

printf 'SERVICE_NAME=checkout\nDATABASE_URL=not-a-url\n' > "$tmp/bad.env"
if node src/cli.js --file "$tmp/bad.env" > "$tmp/bad.out" 2>&1; then
  echo "expected failure for invalid env"
  exit 1
fi
grep -q 'must be an http' "$tmp/bad.out"

rm -rf "$tmp"
echo "smoke: ok"

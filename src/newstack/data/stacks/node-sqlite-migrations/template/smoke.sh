#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-sqlite-migrations"

npm test

tmp=$(mktemp -d)
mkdir -p "$tmp/migrations"
printf 'CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT);\n' > "$tmp/migrations/001.sql"
printf "INSERT INTO t (name) VALUES ('alice');\n" > "$tmp/migrations/002.sql"
node src/cli.js --db "$tmp/app.db" --dir "$tmp/migrations"
node src/cli.js --db "$tmp/app.db" --dir "$tmp/migrations" --status | grep -q '"applied": true'

rm -rf "$tmp"
echo "smoke: ok"

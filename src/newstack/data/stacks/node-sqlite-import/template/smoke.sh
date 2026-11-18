#!/bin/sh
set -eu
tmp=$(mktemp -d)
printf 'name,age\nalice,30\nbob,25\n' > "$tmp/data.csv"
node src/cli.js import "$tmp/data.csv" "$tmp/data.db"
node src/cli.js query "$tmp/data.db" 'SELECT name FROM data ORDER BY name' | grep -q alice
echo ok

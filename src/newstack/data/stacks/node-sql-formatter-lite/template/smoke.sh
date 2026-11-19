#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-sql-formatter-lite"

npm test

node src/cli.js "select id, name from users where active=1" | grep -q 'SELECT id, name FROM users WHERE active=1;'

echo "smoke: PASS"
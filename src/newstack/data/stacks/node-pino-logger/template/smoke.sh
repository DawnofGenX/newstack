#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-pino-logger"

npm test

out=$(node src/cli.js --level info --msg hello --password s3cret)
echo "$out" | grep -q '"msg":"hello"'
echo "$out" | grep -q '\[REDACTED\]'

echo "smoke: ok"

#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-parse-duration-cli"

npm test

node src/cli.js 1h30m | grep -q '^5400000$'

echo "smoke: PASS"
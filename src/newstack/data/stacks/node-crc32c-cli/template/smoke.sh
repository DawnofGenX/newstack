#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-crc32c-cli"

npm test

printf '123456789' | node src/cli.js | grep -q 'E3069283'

echo "smoke: PASS"
#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-totp-cli"

npm test

code=$(node src/cli.js generate --secret JBSWY3DPEHPK3PXP --digits 6)
test -n "$code"
node src/cli.js verify --secret JBSWY3DPEHPK3PXP --code "$code" | grep -q valid

echo "smoke: ok"
#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-hmac-signer-cli"

npm test

ts=$(date +%s)
sig=$(node src/cli.js sign --secret secret --payload "hello" --timestamp "$ts")
echo "signature: $sig"
test "$sig" = "v1=$(node -e "const c=require('crypto');process.stdout.write(c.createHmac('sha256','secret').update('${ts}.hello').digest('hex'))")"

node src/cli.js verify --secret secret --payload "hello" --signature "$sig" --timestamp "$ts"

set +e
node src/cli.js verify --secret secret --payload "tampered" --signature "$sig" --timestamp "$ts" >/dev/null 2>&1
status=$?
set -e
test "$status" -ne 0

echo "smoke: ok"

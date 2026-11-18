#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-jwt-cli"

npm test

secret="smoke-secret"
token=$(node src/cli.js sign --secret "$secret" --payload '{"sub":"alice","scope":"read"}' --ttl 120)
test "$(printf '%s' "$token" | awk -F. '{print NF}')" -eq 3

claims=$(node src/cli.js verify "$token" --secret "$secret")
case "$claims" in
  *'"sub":"alice"'*) ;;
  *) echo "unexpected claims: $claims"; exit 1 ;;
esac

if node src/cli.js verify "$token" --secret other > /dev/null 2>&1; then
  echo "expected verification failure with the wrong secret"
  exit 1
fi

node src/cli.js decode "$token" | grep -q '"typ": "JWT"'

echo "smoke: ok"

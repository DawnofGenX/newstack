#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-otpauth-uri"

npm test

secret="GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
tmp=$(mktemp -d)

code=$(node src/cli.js code --secret "$secret" --counter 0)
test "$code" = "755224"

uri=$(node src/cli.js uri --secret "$secret" --issuer Acme --account alice@example.com)
case "$uri" in
  otpauth://totp/Acme:alice%40example.com*) ;;
  *) echo "unexpected uri: $uri"; exit 1 ;;
esac

node src/cli.js parse "$uri" > "$tmp/parsed.json"
grep -q '"account": "alice@example.com"' "$tmp/parsed.json"
grep -q '"issuer": "Acme"' "$tmp/parsed.json"

rm -rf "$tmp"
echo "smoke: ok"

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
out=$(node src/cli.js "https://Example.COM:443/a/?utm_source=x&b=2&a=1")
echo "$out"
test "$out" = "https://example.com/a?a=1&b=2"
echo "smoke ok"

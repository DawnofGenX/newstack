#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-semver-range-cli"

npm test

node src/cli.js 1.2.3 "^1.0.0" | grep -q "satisfied"
out=$(node src/cli.js 2.0.0 "^1.0.0" 2>/dev/null || true)
echo "$out" | grep -q "not satisfied"
node src/cli.js 1.2.3 "1.0.0 - 2.0.0" | grep -q "satisfied"

echo "smoke: ok"

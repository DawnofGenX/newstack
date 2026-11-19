#!/usr/bin/env bash
set -euo pipefail

echo "smoke: bun-password-strength-cli"

bun test

./bin/{{ npm_name }} 'Tr0ub4dor&3' | grep -q 'strong\|very strong'

echo "smoke: PASS"
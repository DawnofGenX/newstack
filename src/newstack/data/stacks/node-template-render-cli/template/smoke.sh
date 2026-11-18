#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-template-render-cli"

npm test

printf '%s' '{{!greeting}}, {{!name}}!' > /tmp/tpl.txt
printf '%s' '{"greeting":"Hello","name":"<x>"}' > /tmp/ctx.json
out=$(node src/cli.js /tmp/tpl.txt /tmp/ctx.json)
echo "$out"
test "$out" = "Hello, &lt;x&gt;!"

echo "smoke: ok"

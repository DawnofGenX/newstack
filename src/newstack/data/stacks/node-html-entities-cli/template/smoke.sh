#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-html-entities-cli"

npm test

tmp=$(mktemp -d)
printf '<b>"hi"</b>' > "$tmp/in.html"
node src/cli.js "$tmp/in.html" | grep -q '&lt;b&gt;&quot;hi&quot;&lt;/b&gt;'
printf '%s' '&lt;b&gt;hi&lt;/b&gt;' | node src/cli.js --decode | grep -q '<b>hi</b>'

rm -rf "$tmp"
echo "smoke: PASS"
#!/usr/bin/env bash
set -euo pipefail

echo "smoke: {{ npm_name }}"

composer install --no-interaction
vendor/bin/phpunit

out=$(php src/main.php '<p onclick="x()">hi</p><script>alert(1)</script><a href="javascript:1">l</a>')
echo "$out"
echo "$out" | grep -q "<p>hi</p>"
if echo "$out" | grep -qi "script\|onclick\|javascript"; then
    echo "dangerous markup survived sanitising"
    exit 1
fi

echo "smoke: PASS"

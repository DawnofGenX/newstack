#!/usr/bin/env bash
set -euo pipefail

echo "smoke: php-markdown-cli"

composer install --no-interaction
vendor/bin/phpunit

printf '# Hello\n\nThis is **bold**.\n' | php src/main.php | grep -F '<h1>Hello</h1>' >/dev/null
printf '# Hello\n' | php src/main.php | grep -F '<h1>Hello</h1>' >/dev/null

echo "smoke: PASS"

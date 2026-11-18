#!/usr/bin/env bash
set -euo pipefail

echo "smoke: {{ npm_name }}"

composer install --no-interaction
vendor/bin/phpunit
TOKEN=$(php src/main.php sign secret '{"sub":"alice","exp":9999999999}')
php src/main.php verify secret "$TOKEN"

echo "smoke: PASS"

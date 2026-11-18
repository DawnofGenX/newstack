#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "smoke: php-csv-report"

composer install --no-interaction --quiet
vendor/bin/phpunit

tmp=$(mktemp)
printf 'name,dept,score\nalice,eng,10\nbob,eng,20\ncarol,sales,5\n' > "$tmp"
out=$(php src/main.php "$tmp" --group=dept --sum=score)
echo "$out"
echo "$out" | grep -q "rows=3"
echo "$out" | grep -q "eng 2"
echo "$out" | grep -q "sum=35"

echo "smoke: PASS"
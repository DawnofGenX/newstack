#!/usr/bin/env bash
set -euo pipefail

echo "smoke: php-slim-api"

items_file=$(mktemp)
rm -f "$items_file"
export PHP_SLIM_ITEMS_FILE="$items_file"
trap 'rm -f "$items_file"' EXIT

composer install --no-interaction --prefer-dist
vendor/bin/phpunit

if curl -fsS --max-time 2 http://127.0.0.1:5577/health >/dev/null 2>&1; then
  echo "port 5577 already answering"
  exit 1
fi

php -S 127.0.0.1:5577 -t public public/index.php >.php.log 2>&1 &
srv=$!
trap 'kill $srv 2>/dev/null || true; wait $srv 2>/dev/null || true; rm -f .php.log "$items_file"' EXIT

for _ in $(seq 1 60); do
  if curl -fsS --max-time 2 http://127.0.0.1:5577/health >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

body=$(curl -fsS --max-time 10 http://127.0.0.1:5577/health)
echo "health=$body"
echo "$body" | grep -q ok

curl -fsS --max-time 10 -X POST -H 'Content-Type: application/json' -d '{"name":"widget"}' http://127.0.0.1:5577/items >/dev/null
code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 -X POST -H 'Content-Type: application/json' -d '{"name":"gadget"}' http://127.0.0.1:5577/items)
echo "post2_status=$code"
test "$code" = "201"
list=$(curl -fsS --max-time 10 http://127.0.0.1:5577/items)
echo "items=$list"
echo "$list" | grep -q widget
echo "$list" | grep -q gadget

bad=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 -X POST -H 'Content-Type: application/json' -d '{"name":""}' http://127.0.0.1:5577/items)
echo "invalid_status=$bad"
test "$bad" = "422"

kill $srv 2>/dev/null || true
wait $srv 2>/dev/null || true
trap - EXIT
rm -f .php.log "$items_file"

echo "smoke: PASS"

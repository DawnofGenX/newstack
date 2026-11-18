#!/usr/bin/env bash
set -euo pipefail

echo "smoke: php-json-pointer-cli"

composer install --no-interaction --quiet
vendor/bin/phpunit --no-coverage

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
printf '{"name":"demo","tags":["a","b"],"nested":{"id":3}}' > "$work/doc.json"

out=$(php bin/{{ npm_name }} get /nested/id "$work/doc.json")
echo "$out"
test "$out" = "3"

php bin/{{ npm_name }} has /tags/1 "$work/doc.json"
set +e
php bin/{{ npm_name }} has /tags/9 "$work/doc.json"
test $? -eq 1
set -e

renamed=$(php bin/{{ npm_name }} set /name --value '"renamed"' "$work/doc.json")
echo "$renamed" | grep -q '"name":"renamed"'

removed=$(php bin/{{ npm_name }} remove /tags/0 "$work/doc.json")
echo "$removed" | grep -q '"removed":"a"'
echo "$removed" | grep -q '"tags":\["b"\]'

tokens=$(php bin/{{ npm_name }} tokens /a~1b "$work/doc.json")
test "$tokens" = '["a/b"]'

php bin/{{ npm_name }} --help >/dev/null
set +e
php bin/{{ npm_name }} --bogus >/dev/null 2>&1
test $? -eq 2
php bin/{{ npm_name }} get /nope "$work/doc.json" >/dev/null 2>&1
test $? -eq 1
set -e

echo "smoke: PASS"

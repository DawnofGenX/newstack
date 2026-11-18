#!/usr/bin/env bash
set -euo pipefail

echo "smoke: php-mustache-cli"

composer install --no-interaction --no-progress >/dev/null
vendor/bin/phpunit --no-coverage

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

PROG="php bin/{{ npm_name }}"

printf 'Hi {{!name}}!' > "$tmp/t.mustache"
printf '{"name":"Ada"}' > "$tmp/d.json"
test "$($PROG "$tmp/t.mustache" --data "$tmp/d.json")" = "Hi Ada!"

printf '{{!#items}}<{{!.}}>{{!/items}}' > "$tmp/list.mustache"
test "$($PROG "$tmp/list.mustache" --json '{"items":["a","b"]}')" = "<a><b>"

test "$(printf '{{!name}}' | $PROG --json '{"name":"<b>"}')" = "&lt;b&gt;"

set +e
$PROG "$tmp/t.mustache" --json '{oops' >/dev/null 2>&1
bad_json=$?
$PROG --bogus >/dev/null 2>&1
bad_flag=$?
set -e
[ "$bad_json" -eq 1 ]
[ "$bad_flag" -eq 2 ]

$PROG --help >/dev/null
echo "smoke: PASS"

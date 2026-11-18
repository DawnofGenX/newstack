#!/usr/bin/env bash
set -euo pipefail

echo "smoke: php-text-table-cli"

composer install --no-interaction --no-progress >/dev/null
vendor/bin/phpunit --no-coverage

PROG="php bin/{{ npm_name }}"

out=$(printf 'name,score\nalice,3\nbob,12\n' | $PROG --header)
echo "$out"
echo "$out" | grep -qF '| name  | score |'
echo "$out" | grep -qF '| alice | 3     |'

out=$(printf 'a,bb\nxxx,1\n' | $PROG --align-column 1=right)
echo "$out" | grep -qF '| xxx |  1 |'

out=$(printf 'a,b\n' | $PROG --border none)
[ "$out" = "a  b" ]

set +e
printf '' | $PROG >/dev/null 2>&1
status=$?
$PROG --bogus >/dev/null 2>&1
bogus=$?
set -e
echo "empty exit: $status, bogus exit: $bogus"
[ "$status" -eq 1 ]
[ "$bogus" -eq 2 ]

echo "smoke: PASS"

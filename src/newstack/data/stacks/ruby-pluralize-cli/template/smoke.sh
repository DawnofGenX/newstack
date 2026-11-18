#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "smoke: ruby-pluralize-cli"

ruby -cw lib/pluralize.rb >/dev/null
ruby -cw lib/pluralize/cli.rb >/dev/null
rake test

test "$(bin/{{ npm_name }} plural cat)" = "cats"
test "$(bin/{{ npm_name }} plural person child sheep | tr '\n' '|')" = "people|children|sheep|"
test "$(bin/{{ npm_name }} singular cats people)"
test "$(bin/{{ npm_name }} count --count 3 person)" = "3 people"
test "$(printf 'baby\nknife\n' | bin/{{ npm_name }} plural | tr '\n' '|')" = "babies|knives|"

set +e
bin/{{ npm_name }} count cat >/dev/null 2>&1
test $? -eq 2
bin/{{ npm_name }} --bogus plural cat >/dev/null 2>&1
test $? -eq 2
bin/{{ npm_name }} plural --file nope.txt >/dev/null 2>&1
test $? -eq 1
set -e

echo "smoke: PASS"

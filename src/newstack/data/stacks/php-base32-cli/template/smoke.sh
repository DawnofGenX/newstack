#!/usr/bin/env bash
set -euo pipefail

echo "smoke: {{ npm_name }}"

if [ ! -d vendor ]; then
  composer install --no-interaction --prefer-dist
fi

vendor/bin/phpunit

printf 'foobar' | php bin/{{ npm_name }} encode | grep -qx 'MZXW6YTBOI======'
printf 'MZXW6YTBOI======' | php bin/{{ npm_name }} decode | grep -qx 'foobar'
printf 'foobar' | php bin/{{ npm_name }} encode --no-pad | grep -qx 'MZXW6YTBOI'
printf '\x00\x01\x02' | php bin/{{ npm_name }} encode --crockford | grep -qx '000G4'

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf 'foobar' > "$tmp/input.txt"
php bin/{{ npm_name }} encode "$tmp/input.txt" | grep -qx 'MZXW6YTBOI======'

php bin/{{ npm_name }} --help | grep -q 'usage:'
if php bin/{{ npm_name }} bogus >/dev/null 2>&1; then
  echo "expected exit 2 for an unknown command" >&2
  exit 1
fi
if php bin/{{ npm_name }} encode does-not-exist.txt >/dev/null 2>&1; then
  echo "expected exit 1 for a missing file" >&2
  exit 1
fi

echo "smoke: ok"

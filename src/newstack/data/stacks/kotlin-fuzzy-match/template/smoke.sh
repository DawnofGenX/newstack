#!/usr/bin/env bash
set -euo pipefail

echo "smoke: {{ npm_name }}"

gradle test --quiet

out=$(gradle run --quiet --args='--a MARTHA --b MARHTA')
echo "$out"
echo "$out" | grep -q 'jaro-winkler=0.9611'
echo "$out" | grep -q 'match=true'

out=$(gradle run --quiet --args='--a MARTHA --b MARHTA --threshold 0.99')
echo "$out" | grep -q 'match=false'

out=$(gradle run --quiet --args='--a recieve --list receive,relieve,believe')
echo "$out"
echo "$out" | grep -q '^rank 1: receive'

if gradle run --quiet --args='--nope' >/dev/null 2>&1; then
  echo "expected a non-zero exit for an unknown option" >&2
  exit 1
fi

echo "smoke: ok"

#!/usr/bin/env bash
set -euo pipefail

echo "smoke: {{ npm_name }}"

rake test

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/store.json" <<'JSON'
{"store":{"book":[{"title":"A"},{"title":"B"}],"bicycle":{"color":"red"}}}
JSON

bin/{{ npm_name }} '$.store.book[*].title' "$tmp/store.json" | diff -u <(printf '"A"\n"B"\n') -
bin/{{ npm_name }} '$..color' "$tmp/store.json" | grep -qx '"red"'
bin/{{ npm_name }} --count '$.store.book[*]' "$tmp/store.json" | tail -1 | grep -qx 'matched 2'

if bin/{{ npm_name }} '$.missing' "$tmp/store.json" >/dev/null; then
  echo "expected exit 1 when nothing matches" >&2
  exit 1
fi

status=0
bin/{{ npm_name }} 'store.book' "$tmp/store.json" >/dev/null 2>&1 || status=$?
test "$status" -eq 2

status=0
printf 'nope' | bin/{{ npm_name }} '$' >/dev/null 2>&1 || status=$?
test "$status" -eq 3

echo "smoke: ok"

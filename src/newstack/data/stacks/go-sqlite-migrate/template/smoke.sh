#!/bin/sh
set -eu

echo "smoke: go-sqlite-migrate"

go build -o bin/migrate .
DB="$(mktemp).db"
trap 'rm -f "$DB"' EXIT

./bin/migrate up "$DB"
./bin/migrate up "$DB"
out=$(./bin/migrate status "$DB")
echo "$out"
applied=$(printf '%s\n' "$out" | grep -c applied || true)
if [ "$applied" -ne 2 ]; then
  echo "  FAIL expected 2 applied migrations, got $applied"; exit 1
fi
echo "  ok   up + idempotent + status"

echo "smoke: PASS"
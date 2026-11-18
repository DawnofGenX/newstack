#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-cron-cli"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

first=$(./bin/{{ npm_name }} -spec '*/15 * * * *' -from 2024-01-01T00:07:00Z -count 1)
test "$first" = "2024-01-01T00:15:00Z"

lines=$(./bin/{{ npm_name }} -spec '0 9 * * 1-5' -from 2024-01-05T10:00:00Z -count 2 | wc -l | tr -d ' ')
test "$lines" = "2"

if ./bin/{{ npm_name }} -spec '61 * * * *' >/dev/null 2>&1; then
  echo "smoke: an out of range spec must exit 1" >&2
  exit 1
fi
if ./bin/{{ npm_name }} -bogus >/dev/null 2>&1; then
  echo "smoke: an unknown flag must exit 2" >&2
  exit 1
fi

echo "smoke: ok"

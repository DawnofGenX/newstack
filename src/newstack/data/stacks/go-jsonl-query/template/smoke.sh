#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-jsonl-query"

go vet ./...
go test ./...
go build -o bin/jsonlq .

tmp=$(mktemp -d)
printf '{"name":"alice","age":30}\n{"name":"bob","age":25}\n' > "$tmp/data.jsonl"
./bin/jsonlq -file "$tmp/data.jsonl" -select name -where 'age==30' | grep -q 'alice'
count=$(./bin/jsonlq -file "$tmp/data.jsonl" -where 'age==30' -count)
test "$count" = "1"

rm -rf "$tmp"
echo "smoke: ok"
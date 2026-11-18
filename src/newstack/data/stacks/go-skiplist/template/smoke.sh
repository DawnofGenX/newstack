#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-skiplist"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

printf 'banana
apple
cherry
' > /tmp/skiplist-values.txt
out=$(./bin/{{ npm_name }} -file /tmp/skiplist-values.txt)
echo "size=$out"
test "$out" = "3"
res=$(./bin/{{ npm_name }} -file /tmp/skiplist-values.txt -contains apple)
echo "contains apple=$res"
test "$res" = "true"
res=$(./bin/{{ npm_name }} -file /tmp/skiplist-values.txt -contains grape)
echo "contains grape=$res"
test "$res" = "false"

echo "smoke: ok"

#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-hyperloglog"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

tmp=$(mktemp -d)
for i in $(seq 1 1000); do echo "item$i"; done > "$tmp/data.txt"
out=$(./bin/{{ npm_name }} -file "$tmp/data.txt")
echo "estimate=$out"
test "$out" -ge 800
test "$out" -le 1200

rm -rf "$tmp"
echo "smoke: ok"

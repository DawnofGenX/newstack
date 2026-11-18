#!/usr/bin/env bash
set -euo pipefail

echo "smoke: {{ npm_name }}"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf '1\n63\n64\n200\n' > "$tmp/values.txt"

out=$(./bin/{{ npm_name }} -file "$tmp/values.txt" -size 256 -query 'rank=64,select=2,has=63')
echo "$out"
echo "$out" | grep -q "set=4"
echo "$out" | grep -q "rank(64)=2"
echo "$out" | grep -q "select(2)=64"
echo "$out" | grep -q "has(63)=true"

echo "smoke: ok"

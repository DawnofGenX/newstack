#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-cuckoo-filter"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

tmp=$(mktemp -d)
./bin/{{ npm_name }} -add alpha,beta,gamma -has beta,gamma,delta > "$tmp/out.json"
grep -q '"beta": true' "$tmp/out.json"
grep -q '"gamma": true' "$tmp/out.json"
grep -q '"delta": false' "$tmp/out.json"

./bin/{{ npm_name }} -add alpha -del alpha -has alpha > "$tmp/del.json"
grep -q '"alpha": false' "$tmp/del.json"

rm -rf "$tmp"
echo "smoke: ok"

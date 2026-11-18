#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-radix-tree"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

tmp=$(mktemp -d)
./bin/{{ npm_name }} -set romane=1,romanus=2,rubicon=6 -get romane > "$tmp/get.json"
grep -q '"found": true' "$tmp/get.json"
grep -q '"value": "1"' "$tmp/get.json"

./bin/{{ npm_name }} -set romane=1,romanus=2,romulus=3 -match romanesque > "$tmp/match.json"
grep -q '"key": "romane"' "$tmp/match.json"

./bin/{{ npm_name }} -set b=2,a=1 -keys > "$tmp/keys.json"
grep -q '"a"' "$tmp/keys.json"
grep -q '"size": 2' "$tmp/keys.json"

rm -rf "$tmp"
echo "smoke: ok"

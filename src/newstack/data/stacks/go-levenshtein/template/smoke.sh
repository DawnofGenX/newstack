#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-levenshtein"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

tmp=$(mktemp -d)
./bin/{{ npm_name }} -a kitten -b sitting > "$tmp/pair.json"
grep -q '"distance": 3' "$tmp/pair.json"

./bin/{{ npm_name }} -a recieve -list relieve,believe,counter > "$tmp/close.json"
grep -q '"closest": "relieve"' "$tmp/close.json"
grep -q '"withinMax": true' "$tmp/close.json"

rm -rf "$tmp"
echo "smoke: ok"

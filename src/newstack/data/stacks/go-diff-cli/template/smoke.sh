#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-diff-cli"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

tmp=$(mktemp -d)
printf 'a
b
c
' > "$tmp/old.txt"
printf 'a
B
c
d
' > "$tmp/new.txt"
./bin/{{ npm_name }} "$tmp/old.txt" "$tmp/new.txt" > "$tmp/out.txt" || true
cat "$tmp/out.txt"
grep -q -- '-b' "$tmp/out.txt"
grep -q -- '+B' "$tmp/out.txt"
grep -q -- '+d' "$tmp/out.txt"

rm -rf "$tmp"
echo "smoke: ok"

#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-tar-extractor"

go vet ./...
go test ./...
go build -o bin/tarextract .

tmp=$(mktemp -d)
mkdir -p "$tmp/src" "$tmp/out"
printf 'hello' > "$tmp/src/hello.txt"
tar -czf "$tmp/good.tar.gz" -C "$tmp/src" .
./bin/tarextract -in "$tmp/good.tar.gz" -out "$tmp/out"
test -f "$tmp/out/hello.txt"

rm -rf "$tmp"
echo "smoke: ok"
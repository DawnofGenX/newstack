#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-env-loader"

go vet ./...
go test ./...
go build -o bin/envloader .

tmp=$(mktemp -d)
printf 'PORT=4000\nHOST=filehost\nexport DEBUG=true\n' > "$tmp/.env"
./bin/envloader -file "$tmp/.env" | grep -q '"PORT": "4000"'

rm -rf "$tmp"
echo "smoke: ok"
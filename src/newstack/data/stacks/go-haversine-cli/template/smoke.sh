#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-haversine-cli"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

./bin/{{ npm_name }} 0 0 0 0 | grep -q '^0.000$'

echo "smoke: PASS"
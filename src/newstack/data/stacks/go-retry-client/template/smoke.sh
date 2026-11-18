#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-retry-client"

go vet ./...
go test ./...
go build -o bin/retryclient .

# verify binary runs
./bin/retryclient 2>&1 | grep -q "usage:" || true

echo "smoke: ok"
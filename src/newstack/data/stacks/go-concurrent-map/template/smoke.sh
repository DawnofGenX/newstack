#!/usr/bin/env bash
set -euo pipefail
echo "smoke: go-concurrent-map"
go test ./...
go run .
echo "smoke: ok"

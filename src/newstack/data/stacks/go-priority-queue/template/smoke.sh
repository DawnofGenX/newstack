#!/usr/bin/env bash
set -euo pipefail
echo "smoke: go-priority-queue"
go test ./...
printf '3 build\n1 test\n2 lint\n' | go run .
echo "smoke: ok"

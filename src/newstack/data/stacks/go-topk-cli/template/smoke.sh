#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-topk-cli"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

out=$(./bin/{{ npm_name }} -k 2 5 1 9 2 8)
echo "$out" | grep -qx '9'
echo "$out" | grep -qx '8'

echo "smoke: PASS"
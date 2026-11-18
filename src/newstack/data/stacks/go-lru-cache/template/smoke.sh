#!/usr/bin/env bash
set -euo pipefail
echo "smoke: go-lru-cache"
go test ./...
printf 'PUT a 1\nPUT b 2\nPUT c 3\nGET a\nGET b\n' | go run . | tee /tmp/lru.out
grep -q "stats:" /tmp/lru.out
echo "smoke: ok"

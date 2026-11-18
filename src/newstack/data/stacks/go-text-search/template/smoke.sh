#!/usr/bin/env bash
set -euo pipefail
echo "smoke: go-text-search"
go test ./...
printf 'hello world\nhello go\n' > /tmp/ts_sample.txt
go run . hello /tmp/ts_sample.txt | tee /tmp/ts.out
grep -q "hello" /tmp/ts.out
echo "smoke: ok"

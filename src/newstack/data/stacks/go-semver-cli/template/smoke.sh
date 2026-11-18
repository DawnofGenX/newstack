#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-semver-cli"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

out=$(./bin/{{ npm_name }} compare 1.2.3 1.10.0)
test "$out" = "-1"

out=$(./bin/{{ npm_name }} compare 2.0.0 2.0.0)
test "$out" = "0"

out=$(./bin/{{ npm_name }} satisfies 1.9.0 '^1.2.0')
test "$out" = "true"

out=$(./bin/{{ npm_name }} satisfies 2.0.0 '^1.2.0')
test "$out" = "false"

echo "smoke: ok"

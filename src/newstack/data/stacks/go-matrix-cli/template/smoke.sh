#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-matrix-cli"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

printf '[[1,2],[3,4]]' > "$tmp/a.json"
printf '[[0,1],[1,0]]' > "$tmp/b.json"

test "$(bin/{{ npm_name }} det -file "$tmp/a.json")" = "det=-2"
test "$(bin/{{ npm_name }} trace -file "$tmp/a.json")" = "trace=5"
test "$(bin/{{ npm_name }} transpose -file "$tmp/a.json")" = "2x2 [[1,3],[2,4]]"
test "$(bin/{{ npm_name }} mul -file "$tmp/a.json" -with "$tmp/b.json")" = "2x2 [[2,1],[4,3]]"
test "$(bin/{{ npm_name }} identity -size 2)" = "2x2 [[1,0],[0,1]]"

printf '[[1,2],[3]]' > "$tmp/jagged.json"
set +e
bin/{{ npm_name }} det -file "$tmp/jagged.json" > /dev/null 2>"$tmp/err.txt"
code=$?
set -e
test "$code" -eq 1
grep -q 'row 2 has 1 value(s), expected 2' "$tmp/err.txt"

printf '[[1,2,3],[4,5,6]]' > "$tmp/rect.json"
set +e
bin/{{ npm_name }} det -file "$tmp/rect.json" > /dev/null 2>&1
code=$?
set -e
test "$code" -eq 1

set +e
bin/{{ npm_name }} --bogus > /dev/null 2>&1
code=$?
set -e
test "$code" -eq 2

set +e
bin/{{ npm_name }} mul -file "$tmp/a.json" > /dev/null 2>&1
code=$?
set -e
test "$code" -eq 2

echo "smoke: ok"

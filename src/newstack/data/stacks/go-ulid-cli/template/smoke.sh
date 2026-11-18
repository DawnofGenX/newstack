#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-ulid-cli"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

tmp=$(mktemp -d)
./bin/{{ npm_name }} -gen -n 3 > "$tmp/ids.txt"
test "$(wc -l < "$tmp/ids.txt")" -eq 3
while read -r id; do
  test "${#id}" -eq 26
done < "$tmp/ids.txt"

first=$(head -n1 "$tmp/ids.txt")
ts=$(./bin/{{ npm_name }} -parse "$first")
case "$ts" in
  *T*) ;;
  *) echo "unexpected timestamp: $ts"; exit 1 ;;
esac

single=$(./bin/{{ npm_name }} -gen -at 2023-11-14T22:13:20Z)
parsed=$(./bin/{{ npm_name }} -parse "$single")
case "$parsed" in
  2023-11-14T22:13:20Z*) ;;
  *) echo "unexpected parsed timestamp: $parsed"; exit 1 ;;
esac

rm -rf "$tmp"
echo "smoke: ok"

#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-hkdf-cli"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

okm=$(./bin/{{ npm_name }} -salt 000102030405060708090a0b0c -info "$(printf '\360\361\362\363\364\365\366\367\370\371')" -length 42 0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b)
test "$okm" = "3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf34007208d5b887185865"

short=$(printf 'key material' | ./bin/{{ npm_name }} -length 16)
test "${#short}" -eq 32

if ./bin/{{ npm_name }} --bogus >/dev/null 2>&1; then
  echo "smoke: an unknown option must exit 2" >&2
  exit 1
fi
if ./bin/{{ npm_name }} abc >/dev/null 2>&1; then
  echo "smoke: odd length hex must exit 1" >&2
  exit 1
fi

echo "smoke: ok"

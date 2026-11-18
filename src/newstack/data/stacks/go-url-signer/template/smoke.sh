#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-url-signer"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

signed=$(./bin/{{ npm_name }} -secret s3cr3t -path /files/report.pdf -ttl 60s)
case "$signed" in
  /files/report.pdf*exp=*) ;;
  *) echo "unexpected signed url: $signed"; exit 1 ;;
esac

case "$signed" in
  *sig=*) ;;
  *) echo "signed url has no signature: $signed"; exit 1 ;;
esac

# the same path signed twice for different ttls must produce different signatures
short=$(./bin/{{ npm_name }} -secret s3cr3t -path /files/report.pdf -ttl 1s)
if [ "$signed" = "$short" ]; then
  echo "expected distinct expiries to change the url"
  exit 1
fi

if ./bin/{{ npm_name }} -path /files/report.pdf > /dev/null 2>&1; then
  echo "expected failure without a secret"
  exit 1
fi

echo "smoke: ok"

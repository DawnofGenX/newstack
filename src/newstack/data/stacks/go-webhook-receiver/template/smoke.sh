#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-webhook-receiver"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

./bin/{{ npm_name }} &
pid=$!
trap 'kill $pid 2>/dev/null || true' EXIT
sleep 1

curl -sS -X POST http://127.0.0.1:5592/webhook -H 'Content-Type: application/json' -d '{"msg":"hi"}' >/tmp/wh-resp.txt
cat /tmp/wh-resp.txt
curl -sS http://127.0.0.1:5592/events | grep -q 'hi'
curl -sS http://127.0.0.1:5592/health | grep -q ok

kill $pid
trap - EXIT
echo "smoke: ok"

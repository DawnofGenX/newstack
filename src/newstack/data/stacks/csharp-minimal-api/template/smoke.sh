#!/usr/bin/env bash
set -euo pipefail

echo "smoke: csharp-minimal-api"

dotnet build --nologo -warnaserror

if curl -fsS --max-time 2 http://127.0.0.1:5576/health >/dev/null 2>&1; then
  echo "port 5576 already answering"
  exit 1
fi

dotnet bin/Debug/net8.0/{{ npm_name }}.dll --urls http://127.0.0.1:5576 >.csharp.log 2>&1 &
srv=$!
trap 'kill $srv 2>/dev/null || true; wait $srv 2>/dev/null || true; rm -f .csharp.log' EXIT

for _ in $(seq 1 120); do
  if curl -fsS --max-time 2 http://127.0.0.1:5576/health >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

body=$(curl -fsS --max-time 10 http://127.0.0.1:5576/health)
echo "health=$body"
echo "$body" | grep -q ok

curl -fsS --max-time 10 -X POST -H 'Content-Type: application/json' -d '{"Name":"widget"}' http://127.0.0.1:5576/items >/dev/null
list=$(curl -fsS --max-time 10 http://127.0.0.1:5576/items)
echo "items=$list"
echo "$list" | grep -q widget

kill $srv 2>/dev/null || true
wait $srv 2>/dev/null || true
trap - EXIT
rm -f .csharp.log

echo "smoke: PASS"

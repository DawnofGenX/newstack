#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "smoke: csharp-jwt-cli"

dotnet test tests/*.csproj --nologo -v minimal
dotnet build --nologo -v minimal

TOKEN=$(dotnet run --project . -- encode sub=alice --secret s3cr3t)
echo "$TOKEN"
echo "$TOKEN" | grep -q '\.'

dotnet run --project . -- verify "$TOKEN" --secret s3cr3t | grep -q "valid"
if dotnet run --project . -- verify "$TOKEN" --secret wrong >/dev/null 2>&1; then
  echo "expected invalid"; exit 1
else
  echo "invalid secret rejected"
fi

dotnet run --project . -- decode "$TOKEN" | grep -q "payload="

echo "smoke: PASS"
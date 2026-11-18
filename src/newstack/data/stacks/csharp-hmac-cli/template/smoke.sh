#!/usr/bin/env bash
set -euo pipefail

echo "smoke: csharp-hmac-cli"

dotnet test --nologo
dotnet build --nologo

DLL="bin/Debug/net8.0/{{ npm_name }}.dll"

out=$(dotnet "$DLL" sign --key secret --message payload)
echo "$out"
echo "$out" | grep -Eq '^[0-9a-f]{64}$'

again=$(dotnet "$DLL" sign --key secret --message payload)
[ "$out" = "$again" ]

result=$(dotnet "$DLL" verify --key secret --message payload --digest "$out")
echo "$result"
[ "$result" = "match" ]

long=$(dotnet "$DLL" sign --key secret --message payload --algo sha512)
[ "${#long}" -eq 128 ]

set +e
dotnet "$DLL" verify --key wrong --message payload --digest "$out" >/dev/null 2>&1
mismatch=$?
dotnet "$DLL" sign --key secret >/dev/null 2>&1
usage=$?
dotnet "$DLL" sign-file --key secret does-not-exist.txt >/dev/null 2>&1
missing=$?
set -e
echo "mismatch: $mismatch, usage: $usage, missing: $missing"
[ "$mismatch" -eq 1 ]
[ "$usage" -eq 2 ]
[ "$missing" -eq 1 ]

echo "smoke: PASS"

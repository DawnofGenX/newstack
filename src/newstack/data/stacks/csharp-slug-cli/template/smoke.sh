#!/usr/bin/env bash
set -euo pipefail

echo "smoke: csharp-slug-cli"

dotnet test --nologo
dotnet build --nologo

DLL="bin/Debug/net8.0/{{ npm_name }}.dll"

out=$(dotnet "$DLL" "Hello World!!!")
echo "$out"
echo "$out" | grep -qx 'hello-world'

out2=$(dotnet "$DLL" "a!!!b...c")
echo "$out2" | grep -qx 'a-b-c'

echo "smoke: PASS"

#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "smoke: csharp-diff-cli"

dotnet test --nologo
dotnet build --nologo

DLL="bin/Debug/net8.0/{{ npm_name }}.dll"

tmpa=$(mktemp)
tmpb=$(mktemp)
printf 'a\nb\nc\n' > "$tmpa"
printf 'a\nB\nc\n' > "$tmpb"
out=$(dotnet "$DLL" "$tmpa" "$tmpb")
echo "$out"
echo "$out" | grep -q -- '-b'
echo "$out" | grep -q -- '+B'

echo "smoke: PASS"

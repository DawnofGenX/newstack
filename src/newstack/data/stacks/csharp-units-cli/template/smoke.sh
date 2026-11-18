#!/usr/bin/env bash
set -euo pipefail

echo "smoke: {{ npm_name }}"

dotnet test --nologo
dotnet build --nologo

DLL="bin/Debug/net8.0/{{ npm_name }}.dll"

out=$(dotnet "$DLL" convert 10 km mi)
echo "$out"
echo "$out" | grep -qx '6.213712 mi'

out=$(dotnet "$DLL" convert 100 C F)
echo "$out" | grep -qx '212 F'

out=$(dotnet "$DLL" convert 1 lb kg)
echo "$out" | grep -qx '0.453592 kg'

dotnet "$DLL" units temperature | grep -q 'F'
dotnet "$DLL" list | grep -q '^length: m km '

if dotnet "$DLL" convert 1 km kg >/dev/null 2>&1; then
  echo "expected a non-zero exit when crossing dimensions" >&2
  exit 1
fi

if dotnet "$DLL" convert 1 furlong m >/dev/null 2>&1; then
  echo "expected a non-zero exit for an unknown unit" >&2
  exit 1
fi

echo "smoke: PASS"

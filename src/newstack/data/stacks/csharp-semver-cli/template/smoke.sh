#!/usr/bin/env bash
set -euo pipefail

echo "smoke: csharp-semver-cli"

dotnet test --nologo
dotnet build --nologo

DLL="bin/Debug/net8.0/{{ npm_name }}.dll"

out=$(dotnet "$DLL" parse 1.2.3-rc.1)
echo "$out"
echo "$out" | grep -qx 'major=1 minor=2 patch=3'

out=$(dotnet "$DLL" compare 1.0.0-alpha 1.0.0)
echo "$out"
[ "$out" = "-1" ]

out=$(dotnet "$DLL" bump patch 1.2.3)
echo "$out"
[ "$out" = "1.2.4" ]

out=$(dotnet "$DLL" satisfies 1.4.0 '^1.2.3')
echo "$out"
[ "$out" = "true" ]

set +e
dotnet "$DLL" satisfies 2.0.0 '^1.2.3' >/dev/null 2>&1
status=$?
dotnet "$DLL" --bogus >/dev/null 2>&1
bogus=$?
set -e
echo "range-miss exit: $status, bogus exit: $bogus"
[ "$status" -eq 1 ]
[ "$bogus" -eq 2 ]

echo "smoke: PASS"

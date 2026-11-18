#!/usr/bin/env bash
set -euo pipefail

echo "smoke: csharp-ini-cli"

dotnet test --nologo
dotnet build --nologo

DLL="bin/Debug/net8.0/{{ npm_name }}.dll"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

printf 'top = 1\n[server]\nhost = localhost\nport = 8080\n' > "$work/a.ini"
printf '[server]\nport = 9090\n[extra]\nflag = on\n' > "$work/b.ini"

out=$(dotnet "$DLL" "$work/a.ini")
echo "$out"
echo "$out" | grep -q '"port": "8080"'

merged=$(dotnet "$DLL" "$work/a.ini" "$work/b.ini" --get server.port)
test "$merged" = "9090"

dotnet "$DLL" "$work/a.ini" "$work/b.ini" --list-sections | grep -qx 'extra'
dotnet "$DLL" "$work/a.ini" --section server | grep -q '"host": "localhost"'
dotnet "$DLL" "$work/a.ini" --ini | grep -qx 'top = 1'

echo "smoke: PASS"

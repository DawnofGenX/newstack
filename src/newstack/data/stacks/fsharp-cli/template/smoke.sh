#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

run() {
  set +e
  OUT=$("$@" 2>&1)
  STATUS=$?
  set -e
}

if ! command -v dotnet >/dev/null 2>&1; then
  echo "smoke: dotnet is missing (install dotnet)"
  exit 1
fi

echo "smoke: fsharp-cli"

run dotnet build App.fsproj -c Release --nologo
if [ "$STATUS" -eq 0 ]; then ok "dotnet build"; else bad "dotnet build"; printf '%s\n' "$OUT" | tail -8; fi

run dotnet test Tests/Tests.fsproj --nologo
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

dll="bin/Debug/net8.0/{{ npm_name }}.dll"
if [ -f "$dll" ]; then
  ok "build output exists"
  set +e
  dotnet "$dll" --help >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

  set +e
  dotnet "$dll" --bogus >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

  set +e
  dotnet "$dll" does-not-exist.txt >/dev/null 2>&1
  st=$?
  set -e
  if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi

  printf 'one two\nthree\n' > sample.txt
  if dotnet "$dll" sample.txt | grep -Eq '^ *2 +3 +14 +sample\.txt$'; then ok "word count output"; else bad "word count output"; fi
  rm -f sample.txt
else
  bad "build output exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
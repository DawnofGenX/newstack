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
  echo "smoke: dotnet is missing (install the .NET 8 SDK)"
  exit 1
fi

echo "smoke: {{ npm_name }}"

run dotnet build --nologo -v quiet
if [ "$STATUS" -eq 0 ]; then ok "dotnet build"; else bad "dotnet build"; printf '%s\n' "$OUT" | tail -8; fi

run dotnet test --nologo -v quiet
if [ "$STATUS" -eq 0 ]; then ok "dotnet test"; else bad "dotnet test"; printf '%s\n' "$OUT" | tail -8; fi

app="bin/Debug/net8.0/{{ npm_name }}"

run "$app" parse 1h30m
if [ "$OUT" = "seconds=5400
iso=PT1H30M
human=1h30m" ]; then ok "parse prints seconds, iso and human"; else bad "parse prints seconds, iso and human"; printf '       got: %s\n' "$OUT"; fi

run "$app" add P1D --from 2026-01-31T23:30:00Z
case $OUT in
  *to=2026-02-01T23:30:00Z*) ok "add crosses the month boundary" ;;
  *) bad "add crosses the month boundary"; printf '       got: %s\n' "$OUT" ;;
esac

run "$app" between 2026-01-01T00:00:00Z 2026-01-02T01:00:00Z
case $OUT in
  *human=1d1h*) ok "between reports the difference" ;;
  *) bad "between reports the difference"; printf '       got: %s\n' "$OUT" ;;
esac

set +e
"$app" parse P1Y >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "calendar months are refused"; else bad "calendar months are refused"; fi

set +e
"$app" frobnicate >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 2 ]; then ok "unknown command exits 2"; else bad "unknown command exits 2"; fi

run "$app" --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

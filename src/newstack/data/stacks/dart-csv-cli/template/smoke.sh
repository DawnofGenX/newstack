#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v dart >/dev/null 2>&1; then
  echo "smoke: dart is missing (install dart)"
  exit 1
fi

echo "smoke: dart-csv-cli"

printf 'name,city\nanna,delhi\nbo,poona\n' > "$work/sample.csv"

if (dart pub get); then ok "get"; else bad "get"; fi
if (dart analyze --fatal-infos); then ok "analyze"; else bad "analyze"; fi
if (dart test); then ok "test"; else bad "test"; fi
if (dart run bin/{{ npm_name }}.dart --help >/dev/null); then ok "help"; else bad "help"; fi

got=$(dart run bin/{{ npm_name }}.dart -c city "$work/sample.csv")
if [ "$got" = 'city
delhi
poona' ]; then ok "column projection"; else bad "column projection"; printf '       got: %s\n' "$got"; fi

got=$(dart run bin/{{ npm_name }}.dart --json "$work/sample.csv")
case "$got" in
  *'"name":"anna"'*) ok "json output" ;;
  *) bad "json output"; printf '       got: %s\n' "$got" ;;
esac

if (dart run bin/{{ npm_name }}.dart --bogus >/dev/null 2>&1; test $? -eq 2); then ok "usage error exits 2"; else bad "usage error exits 2"; fi
if (dart run bin/{{ npm_name }}.dart no-such-file.csv >/dev/null 2>&1; test $? -eq 1); then ok "missing file exits 1"; else bad "missing file exits 1"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

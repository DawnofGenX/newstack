#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v crystal >/dev/null 2>&1; then
  case "crystal" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: crystal is missing (install crystal)"; exit 1 ;;
  esac
fi

echo "smoke: crystal-cli"

if (
crystal spec
); then ok "test"; else bad "test"; fi

if (
mkdir -p bin && crystal build -o bin/{{ npm_name }} src/textstat.cr
); then ok "build"; else bad "build"; fi

if (
./bin/{{ npm_name }} --help
); then ok "help"; else bad "help"; fi

if (
./bin/{{ npm_name }} --bogus >/dev/null 2>&1; test $? -eq 2
); then ok "usage-error"; else bad "usage-error"; fi

if (
./bin/{{ npm_name }} does-not-exist.txt >/dev/null 2>&1; test $? -eq 1
); then ok "missing-file"; else bad "missing-file"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

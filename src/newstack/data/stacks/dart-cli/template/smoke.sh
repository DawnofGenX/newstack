#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

if ! command -v dart >/dev/null 2>&1; then
  case "dart" in
    guile-json|lua-socket|lua-cjson|fp-units-fcl) : ;;
    *) echo "smoke: dart is missing (install dart)"; exit 1 ;;
  esac
fi

echo "smoke: dart-cli"

if (
dart pub get
); then ok "get"; else bad "get"; fi

if (
dart analyze --fatal-infos
); then ok "analyze"; else bad "analyze"; fi

if (
dart test
); then ok "test"; else bad "test"; fi

if (
dart run bin/{{ npm_name }}.dart --help
); then ok "help"; else bad "help"; fi

if (
dart run bin/{{ npm_name }}.dart --bogus >/dev/null 2>&1; test $? -eq 2
); then ok "usage-error"; else bad "usage-error"; fi

if (
dart run bin/{{ npm_name }}.dart does-not-exist.txt >/dev/null 2>&1; test $? -eq 1
); then ok "missing-file"; else bad "missing-file"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

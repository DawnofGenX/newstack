#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

if ! command -v dart >/dev/null 2>&1; then
  echo "smoke: dart is missing (install dart)"; exit 1
fi

echo "smoke: dart-uuid-cli"

if ( dart pub get ); then ok "get"; else bad "get"; fi
if ( dart analyze --fatal-infos ); then ok "analyze"; else bad "analyze"; fi
if ( dart test ); then ok "test"; else bad "test"; fi
if ( dart run bin/{{ npm_name }}.dart --help ); then ok "help"; else bad "help"; fi
if ( dart run bin/{{ npm_name }}.dart --bogus >/dev/null 2>&1; test $? -eq 2 ); then ok "usage-error"; else bad "usage-error"; fi
if ( u=$(dart run bin/{{ npm_name }}.dart gen v4) && [ -n "$u" ] ); then ok "gen"; else bad "gen"; fi
if ( dart run bin/{{ npm_name }}.dart validate 550e8400-e29b-41d4-a716-446655440000 ); then ok "validate"; else bad "validate"; fi
if ( dart run bin/{{ npm_name }}.dart validate not-a-uuid >/dev/null 2>&1; test $? -eq 1 ); then ok "validate-bad"; else bad "validate-bad"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
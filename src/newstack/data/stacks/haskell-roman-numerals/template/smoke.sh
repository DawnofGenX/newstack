#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }

if ! command -v ghc >/dev/null 2>&1; then echo "smoke: ghc is missing"; exit 1; fi
if ! command -v cabal >/dev/null 2>&1; then echo "smoke: cabal is missing"; exit 1; fi

echo "smoke: haskell-roman-numerals"

if (cabal build all); then ok "build"; else bad "build"; fi
if (cabal test all); then ok "test"; else bad "test"; fi
if (test "$(./bin/{{ npm_name }} --encode 1990)" = "MCMXC"); then ok "encode"; else bad "encode"; fi
if (test "$(./bin/{{ npm_name }} --decode MCMXC)" = "1990"); then ok "decode"; else bad "decode"; fi
if (set +e; ./bin/{{ npm_name }} --bogus >/dev/null 2>&1; status=$?; test "$status" -eq 2); then ok "usage-error"; else bad "usage-error"; fi
if (set +e; ./bin/{{ npm_name }} --decode IIII >/dev/null 2>&1; status=$?; test "$status" -eq 1); then ok "invalid"; else bad "invalid"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

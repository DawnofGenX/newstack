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

echo "smoke: {{ npm_name }}"

run rake test
if [ "$STATUS" -eq 0 ]; then ok "rake test"; else bad "rake test"; printf '%s\n' "$OUT"; fi

run bin/{{ npm_name }} compare 1.0.0 2.0.0
if [ "$OUT" = "-1" ]; then ok "compare"; else bad "compare"; printf '       got: %s\n' "$OUT"; fi

run bin/{{ npm_name }} validate 1.2.3-rc.1
if [ "$OUT" = "valid" ]; then ok "validate"; else bad "validate"; printf '       got: %s\n' "$OUT"; fi

run bin/{{ npm_name }} sort 2.0.0 1.0.0 1.5.0
if [ "$OUT" = "1.0.0
1.5.0
2.0.0" ]; then ok "sort"; else bad "sort"; printf '       got: %s\n' "$OUT"; fi

run bin/{{ npm_name }} bump 1.2.3 minor
if [ "$OUT" = "1.3.0" ]; then ok "bump"; else bad "bump"; printf '       got: %s\n' "$OUT"; fi

run bin/{{ npm_name }} frobnicate
if [ "$STATUS" -eq 2 ]; then ok "usage error exits 2"; else bad "usage error exits 2"; fi

run bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
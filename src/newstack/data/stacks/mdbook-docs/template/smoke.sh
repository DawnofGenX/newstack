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

if ! command -v mdbook >/dev/null 2>&1; then
  echo "smoke: mdbook is missing (install mdbook)"
  exit 1
fi
if ! command -v make >/dev/null 2>&1; then
  echo "smoke: make is missing (install make)"
  exit 1
fi

echo "smoke: mdbook-docs"

run make -s build
if [ "$STATUS" -eq 0 ]; then ok "mdbook build passes"; else bad "mdbook build passes"; printf '%s\n' "$OUT" | tail -8; fi

if [ -f book/index.html ] && [ -f book/guide/writing.html ]; then ok "book artifacts exist"; else bad "book artifacts exist"; fi

run ./tools/check-links.sh
if [ "$STATUS" -eq 0 ]; then ok "link check passes"; else bad "link check passes"; printf '%s\n' "$OUT" | tail -8; fi

run ./tests/run_tests.sh
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
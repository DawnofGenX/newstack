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

if ! command -v perl >/dev/null 2>&1; then
  echo "smoke: perl is missing (install perl)"
  exit 1
fi

echo "smoke: perl-cli"

run perl Makefile.PL
if [ "$STATUS" -eq 0 ]; then ok "Makefile.PL runs"; else bad "Makefile.PL runs"; fi

run make
if [ "$STATUS" -eq 0 ]; then ok "make builds"; else bad "make builds"; fi

run make test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

run perl bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

set +e
perl bin/{{ npm_name }} --bogus >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

set +e
perl bin/{{ npm_name }} does-not-exist.txt >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
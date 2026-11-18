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

echo "smoke: {{ npm_name }}"

run perl Makefile.PL
if [ "$STATUS" -eq 0 ]; then ok "Makefile.PL runs"; else bad "Makefile.PL runs"; fi

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
perl bin/{{ npm_name }} nope.ini >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi

got=$(printf '[server]\nhost = localhost\n' | perl bin/{{ npm_name }} -g server.host)
if [ "$got" = "localhost" ]; then ok "value lookup"; else bad "value lookup"; printf '       got: %s\n' "$got"; fi

got=$(printf '[a]\nx = 1\n' | perl bin/{{ npm_name }} --list-sections)
if [ "$got" = "a" ]; then ok "section listing"; else bad "section listing"; printf '       got: %s\n' "$got"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

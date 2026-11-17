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

if ! command -v gawk >/dev/null 2>&1; then
  echo "smoke: gawk is missing (install gawk)"
  exit 1
fi

echo "smoke: awk-cli"

got=$(printf 'alpha beta\ngamma delta\n' | ./bin/{{ npm_name }})
if [ "$got" = '      2       4      23' ]; then ok "default output"; else bad "default output"; printf '       got: %s\n' "$got"; fi

got=$(printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w)
if [ "$got" = '3' ]; then ok "word count on stdin"; else bad "word count on stdin"; printf '       got: %s\n' "$got"; fi

got=$(printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w -)
if [ "$got" = '3 -' ]; then ok "explicit stdin operand"; else bad "explicit stdin operand"; printf '       got: %s\n' "$got"; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

set +e
./bin/{{ npm_name }} /nonexistent/file.txt >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi

run env LC_ALL=C gawk -f lib/counts.awk -f lib/options.awk -f lib/runner.awk -f tests/harness.awk -f tests/run_tests.awk
if [ "$STATUS" -eq 0 ]; then ok "in-process suite passes"; else bad "in-process suite passes"; printf '%s\n' "$OUT"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
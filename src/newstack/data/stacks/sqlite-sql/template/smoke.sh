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

if ! command -v sqlite3 >/dev/null 2>&1; then
  echo "smoke: sqlite3 is missing (install sqlite3)"
  exit 1
fi
if ! command -v make >/dev/null 2>&1; then
  echo "smoke: make is missing (install make)"
  exit 1
fi

echo "smoke: sqlite-sql"

run make -s db
if [ "$STATUS" -eq 0 ]; then ok "make db passes"; else bad "make db passes"; fi

if [ -f build/app.db ]; then ok "database artifact exists"; else bad "database artifact exists"; fi

got=$(sqlite3 build/app.db 'PRAGMA integrity_check;')
if [ "$got" = "ok" ]; then ok "integrity check"; else bad "integrity check"; printf '       got: %s\n' "$got"; fi

out=$(./bin/{{ npm_name }} top_customers | head -1)
if printf '%s\n' "$out" | grep -qxF 'Bruno|2|87.00'; then ok "report first row"; else bad "report first row"; printf '       got: %s\n' "$out"; fi

run sh tests/run_tests.sh
if [ "$STATUS" -eq 0 ]; then ok "tests pass"; else bad "tests pass"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
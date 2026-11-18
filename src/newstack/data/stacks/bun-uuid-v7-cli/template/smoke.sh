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

if ! command -v bun >/dev/null 2>&1; then
  echo "smoke: bun is missing (install bun)"
  exit 1
fi

echo "smoke: {{ npm_name }}"

run bun test
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

one=$(./bin/{{ npm_name }} gen)
case $one in
  *-7*-*) ok "gen prints a v7 uuid" ;;
  *) bad "gen prints a v7 uuid"; printf '       got: %s\n' "$one" ;;
esac

lines=$(./bin/{{ npm_name }} gen --count 3 | wc -l | tr -d ' ')
if [ "$lines" = '3' ]; then ok "gen --count 3 prints three"; else bad "gen --count 3 prints three"; fi

run ./bin/{{ npm_name }} parse "$one"
case $OUT in
  *version=7*) ok "parse reports version 7" ;;
  *) bad "parse reports version 7"; printf '       got: %s\n' "$OUT" ;;
esac

set +e
./bin/{{ npm_name }} validate not-a-uuid >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "invalid uuid exits 1"; else bad "invalid uuid exits 1"; fi

set +e
./bin/{{ npm_name }} frobnicate >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 2 ]; then ok "unknown command exits 2"; else bad "unknown command exits 2"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

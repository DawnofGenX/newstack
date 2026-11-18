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

set +e
OUT=$(printf 'one two three' | bin/{{ npm_name }} -w 7)
STATUS=$?
set -e
if [ "$OUT" = "one two
three" ]; then ok "wraps standard input"; else bad "wraps standard input"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(printf 'aaa bbb\n\nccc' | bin/{{ npm_name }} -w 5)
set -e
if [ "$OUT" = "aaa
bbb

ccc" ]; then ok "keeps the paragraph break"; else bad "keeps the paragraph break"; printf '       got: %s\n' "$OUT"; fi

run bin/{{ npm_name }} -w 0
if [ "$STATUS" -eq 2 ]; then ok "a zero width exits 2"; else bad "a zero width exits 2"; fi

run bin/{{ npm_name }} /nonexistent/file.txt
if [ "$STATUS" -eq 1 ]; then ok "a missing file exits 1"; else bad "a missing file exits 1"; fi

run bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

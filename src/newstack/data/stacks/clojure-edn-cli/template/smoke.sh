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

if ! command -v clojure >/dev/null 2>&1; then
  echo "smoke: clojure is missing (install clojure)"
  exit 1
fi
if ! command -v java >/dev/null 2>&1; then
  echo "smoke: java is missing (install java)"
  exit 1
fi

echo "smoke: clojure-edn-cli"

run clojure -M -e "(require 'edncli.cli)"
if [ "$STATUS" -eq 0 ]; then ok "clojure loads"; else bad "clojure loads"; printf '%s\n' "$OUT" | tail -8; fi

run clojure -M:test -m edncli.run-tests
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -8; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; printf '%s\n' "$OUT" | tail -8; fi

set +e
./bin/{{ npm_name }} frobnicate >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 2 ]; then ok "bad usage exits 2"; else bad "bad usage exits 2"; fi

set +e
./bin/{{ npm_name }} pretty nope.edn >/dev/null 2>&1
st=$?
set -e
if [ "$st" -eq 1 ]; then ok "missing file exits 1"; else bad "missing file exits 1"; fi

out=$(printf '{:a 1}' | ./bin/{{ npm_name }} pretty -)
if [ -n "$out" ]; then ok "stdin pretty"; else bad "stdin pretty"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
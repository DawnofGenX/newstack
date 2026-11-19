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

if ! command -v tclsh >/dev/null 2>&1; then
  echo "smoke: tclsh is missing (install tcl)"
  exit 1
fi

echo "smoke: {{ package_name }}"

run tclsh tests/run.tcl
if [ "$STATUS" -eq 0 ]; then ok "test suite passes"; else bad "test suite passes"; printf '%s\n' "$OUT" | tail -5; fi

run ./bin/{{ npm_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

set +e
OUT=$(./bin/{{ npm_name }} encode -t foobar)
STATUS=$?
set -e
if [ "$OUT" = "Zm9vYmFy" ]; then ok "encode matches RFC 4648"; else bad "encode matches RFC 4648"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(./bin/{{ npm_name }} decode -t Zm9vYmFy)
STATUS=$?
set -e
if [ "$OUT" = "foobar" ]; then ok "decode round-trips"; else bad "decode round-trips"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(printf 'hello' | ./bin/{{ npm_name }} encode)
STATUS=$?
set -e
if [ "$OUT" = "aGVsbG8=" ]; then ok "stdin is the default input"; else bad "stdin is the default input"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(./bin/{{ npm_name }} encode --url --no-padding -t '<<??>>')
STATUS=$?
set -e
if [ "$OUT" = "PDw_Pz4-" ]; then ok "url-safe alphabet drops padding"; else bad "url-safe alphabet drops padding"; printf '       got: %s\n' "$OUT"; fi

set +e
OUT=$(./bin/{{ npm_name }} decode -t 'PDw_Pz4-')
STATUS=$?
set -e
if [ "$OUT" = '<<??>>' ]; then ok "url-safe input decodes"; else bad "url-safe input decodes"; printf '       got: %s\n' "$OUT"; fi

run ./bin/{{ npm_name }} decode -t 'not base64!!'
if [ "$STATUS" -eq 1 ]; then ok "invalid input exits 1"; else bad "invalid input exits 1"; fi

run ./bin/{{ npm_name }} frobnicate
if [ "$STATUS" -eq 2 ]; then ok "a usage error exits 2"; else bad "a usage error exits 2"; fi

run ./bin/{{ npm_name }} encode does-not-exist.txt
if [ "$STATUS" -eq 1 ]; then ok "a missing file exits 1"; else bad "a missing file exits 1"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

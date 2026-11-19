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

if ! command -v nim >/dev/null 2>&1 || ! command -v nimble >/dev/null 2>&1; then
  echo "smoke: nim and nimble are required"
  exit 1
fi

echo "smoke: {{ package_name }}"

run nimble build
if [ "$STATUS" -eq 0 ]; then ok "nimble build"; else bad "nimble build"; printf '%s\n' "$OUT"; fi

run ./{{ package_name }} encode hello
if [ "$OUT" = "aGVsbG8=" ]; then ok "encode"; else bad "encode"; printf '       got: %s\n' "$OUT"; fi

run ./{{ package_name }} decode aGVsbG8=
if [ "$OUT" = "hello" ]; then ok "decode"; else bad "decode"; printf '       got: %s\n' "$OUT"; fi

run ./{{ package_name }} encode --no-padding hello
if [ "$OUT" = "aGVsbG8" ]; then ok "no padding"; else bad "no padding"; printf '       got: %s\n' "$OUT"; fi

run ./{{ package_name }} encode --url '???'
if [ "$OUT" = "Pz8_" ]; then ok "url-safe alphabet"; else bad "url-safe alphabet"; printf '       got: %s\n' "$OUT"; fi

run ./{{ package_name }} decode notbase64
if [ "$STATUS" -eq 1 ]; then ok "bad input exits 1"; else bad "bad input exits 1"; fi

run ./{{ package_name }} encode --bogus
if [ "$STATUS" -eq 2 ]; then ok "an unknown option exits 2"; else bad "an unknown option exits 2"; fi

run ./{{ package_name }} --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

set +e
OUT=$(printf 'hello' | ./{{ package_name }} encode)
STATUS=$?
set -e
if [ "$OUT" = "aGVsbG8=" ]; then ok "standard input is encoded"; else bad "standard input is encoded"; printf '       got: %s\n' "$OUT"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

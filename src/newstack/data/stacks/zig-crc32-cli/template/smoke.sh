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

if ! command -v zig >/dev/null 2>&1; then
  echo "smoke: zig is required"
  exit 1
fi

echo "smoke: {{ package_name }}"

run zig build test
if [ "$STATUS" -eq 0 ]; then ok "zig build test"; else bad "zig build test"; printf '%s\n' "$OUT"; fi

run zig build
if [ "$STATUS" -eq 0 ]; then ok "zig build"; else bad "zig build"; printf '%s\n' "$OUT"; fi

BIN=zig-out/bin/{{ package_name }}

run "$BIN" --string 123456789
if [ "$OUT" = "cbf43926" ]; then ok "the standard check vector"; else bad "the standard check vector"; printf '       got: %s\n' "$OUT"; fi

run "$BIN" --string ""
if [ "$OUT" = "00000000" ]; then ok "the empty string hashes to zero"; else bad "the empty string hashes to zero"; printf '       got: %s\n' "$OUT"; fi

run "$BIN" --string abc
if [ "$OUT" = "352441c2" ]; then ok "abc"; else bad "abc"; printf '       got: %s\n' "$OUT"; fi

run "$BIN" --string 123456789 --check cbf43926
if [ "$STATUS" -eq 0 ]; then ok "a matching --check exits 0"; else bad "a matching --check exits 0"; fi

run "$BIN" --string 123456789 --check 00000000
if [ "$STATUS" -eq 1 ]; then ok "a mismatched --check exits 1"; else bad "a mismatched --check exits 1"; fi

run "$BIN" --check cbf43926
if [ "$STATUS" -eq 2 ]; then ok "a missing input exits 2"; else bad "a missing input exits 2"; fi

run "$BIN" --bogus
if [ "$STATUS" -eq 2 ]; then ok "an unknown flag exits 2"; else bad "an unknown flag exits 2"; fi

run "$BIN" --help
if [ "$STATUS" -eq 0 ]; then ok "help exits 0"; else bad "help exits 0"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

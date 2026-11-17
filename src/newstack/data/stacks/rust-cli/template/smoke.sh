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

if ! command -v cargo >/dev/null 2>&1; then
  echo "smoke: cargo is missing (install rust)"
  exit 1
fi

echo "smoke: rust-cli"

run cargo test
if [ "$STATUS" -eq 0 ]; then ok "cargo test passes"; else bad "cargo test passes"; printf '%s\n' "$OUT" | tail -8; fi

run cargo build --release
if [ "$STATUS" -eq 0 ]; then ok "cargo build --release"; else bad "cargo build --release"; fi

BIN=./target/release/{{ npm_name }}
if [ -x "$BIN" ]; then
  got=$("$BIN" greet --name smoke)
  if [ "$got" = 'Hello, smoke!' ]; then ok "binary greets smoke"; else bad "binary greets smoke"; printf '       got: %s\n' "$got"; fi

  got=$("$BIN" --version)
  if [ "$got" = '0.1.0' ]; then ok "binary version"; else bad "binary version"; printf '       got: %s\n' "$got"; fi
else
  bad "binary exists"
fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
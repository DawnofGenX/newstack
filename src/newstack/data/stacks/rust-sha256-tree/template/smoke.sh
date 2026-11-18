#!/bin/sh
set -eu

PASSED=0
FAILED=0

ok() { PASSED=$((PASSED + 1)); printf '  ok   %s\n' "$1"; }
bad() { FAILED=$((FAILED + 1)); printf '  FAIL %s\n' "$1"; }
run() { set +e; OUT=$("$@" 2>&1); STATUS=$?; set -e; }

echo "smoke: {{ npm_name }}"

run cargo fmt --check
if [ "$STATUS" -eq 0 ]; then ok "cargo fmt"; else bad "cargo fmt"; printf '%s\n' "$OUT" | tail -5; fi

run cargo clippy --all-targets -- -D warnings
if [ "$STATUS" -eq 0 ]; then ok "clippy"; else bad "clippy"; printf '%s\n' "$OUT" | tail -8; fi

run cargo test
if [ "$STATUS" -eq 0 ]; then ok "tests"; else bad "tests"; printf '%s\n' "$OUT" | tail -8; fi

run cargo build --release
if [ "$STATUS" -eq 0 ]; then ok "build"; else bad "build"; printf '%s\n' "$OUT" | tail -8; fi

# root digest deterministic
run sh -c "printf 'a' > /tmp/sa && printf 'b' > /tmp/sb && ./target/release/{{ npm_name }} /tmp/sa /tmp/sb"
if [ "$STATUS" -eq 0 ]; then ok "root prints"; else bad "root prints"; printf '%s\n' "$OUT"; fi

# inclusion proof
run sh -c "printf 'a' > /tmp/sa && printf 'b' > /tmp/sb && ./target/release/{{ npm_name }} --proof /tmp/sa /tmp/sa /tmp/sb"
if [ "$STATUS" -eq 0 ]; then ok "proof verifies"; else bad "proof verifies"; printf '%s\n' "$OUT"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

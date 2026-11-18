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

# RFC 4648 vector
run sh -c "printf 'foobar' | ./target/release/{{ npm_name }}"
if [ "$STATUS" -eq 0 ] && [ "$OUT" = "Zm9vYmFy" ]; then ok "rfc4648 vector"; else bad "rfc4648 vector"; printf 'got: %s\n' "$OUT"; fi

# round trip
run sh -c "printf 'hello world' | ./target/release/{{ npm_name }} | ./target/release/{{ npm_name }} -d"
if [ "$STATUS" -eq 0 ]; then ok "round trip"; else bad "round trip"; printf '%s\n' "$OUT"; fi

# bad input exit code
run sh -c "printf '!!!!' | ./target/release/{{ npm_name }} -d"
if [ "$STATUS" -eq 1 ]; then ok "bad input exits 1"; else bad "bad input exits 1"; printf 'status=%s\n' "$STATUS"; fi

# url-safe + no-pad
run sh -c "printf 'hello world' | ./target/release/{{ npm_name }} --url-safe --no-pad"
if [ "$STATUS" -eq 0 ]; then ok "url-safe no-pad"; else bad "url-safe no-pad"; printf '%s\n' "$OUT"; fi

printf 'smoke: %d passed, %d failed\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]

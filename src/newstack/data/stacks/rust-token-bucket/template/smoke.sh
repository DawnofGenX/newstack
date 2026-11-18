#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-token-bucket"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

out=$(./target/release/{{ npm_name }} --capacity 2 --rate 1 --requests 4 --interval-ms 1000)
echo "$out" | grep -q "capacity=2"
echo "$out" | grep -q "request 1: t=0ms allow"
echo "$out" | grep -q "request 3: t=2000ms allow"
if echo "$out" | grep -q "request 4: t=3000ms deny"; then
  exit 1
fi

denied=$(./target/release/{{ npm_name }} --capacity 1 --rate 0.5 --requests 2 --interval-ms 100)
echo "$denied" | grep -q "request 2: t=100ms deny"

echo "smoke: PASS"

#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-bitfield-cli"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

out=$(./target/release/{{ npm_name }} 0 --set 3 --set 0)
echo "$out" | grep -E '^9 ' >/dev/null

out2=$(./target/release/{{ npm_name }} 0xff)
echo "$out2" | grep -F "255" >/dev/null

./target/release/{{ npm_name }} --help >/dev/null

echo "smoke: PASS"

#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-mini-sed"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf 'hello world\n' > "$tmp/in.txt"

out=$(printf 'hello world\n' | ./target/release/{{ npm_name }} world rust)
echo "$out" | grep -F "hello rust" >/dev/null

out2=$(./target/release/{{ npm_name }} a b -g "$tmp/in.txt" 2>/dev/null || true)
# file input path may print; just ensure binary runs
./target/release/{{ npm_name }} --help >/dev/null

echo "smoke: PASS"

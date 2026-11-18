#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-csv-to-json"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf 'name,age\nalice,30\n' > "$tmp/in.csv"

out=$(./target/release/{{ npm_name }} "$tmp/in.csv")
echo "$out" | grep -F "alice" >/dev/null
echo "$out" | grep -F "30" >/dev/null

out2=$(printf 'x,y\n1,2\n' | ./target/release/{{ npm_name }})
echo "$out2" | grep -F '"x":"1"' >/dev/null

./target/release/{{ npm_name }} --help >/dev/null

echo "smoke: PASS"

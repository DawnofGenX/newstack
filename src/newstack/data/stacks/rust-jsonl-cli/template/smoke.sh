#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-jsonl-cli"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

tmp=$(mktemp -d)
printf '{"name":"alice","age":30}\n{"name":"bob","age":25}\n' > "$tmp/data.jsonl"
./target/release/{{ npm_name }} -file "$tmp/data.jsonl" -select name -where 'age==30' | grep -q 'alice'
count=$(./target/release/{{ npm_name }} -file "$tmp/data.jsonl" -count)
test "$count" = "2"

rm -rf "$tmp"
echo "smoke: PASS"
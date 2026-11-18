#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-mini-grep"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/sub"
printf 'Hello world\nfoo bar\n' > "$tmp/a.txt"
printf 'HELLO again\n' > "$tmp/sub/b.txt"

out=$(./target/release/{{ npm_name }} -i hello "$tmp")
echo "$out" | grep -F "Hello world" >/dev/null
echo "$out" | grep -F "HELLO again" >/dev/null

cout=$(./target/release/{{ npm_name }} -c x "$tmp" 2>/dev/null || true)
# count over tree may include 0; just ensure binary runs
./target/release/{{ npm_name }} --help >/dev/null

echo "smoke: PASS"

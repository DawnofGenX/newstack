#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-hex-dump-cli"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf 'AB' > "$tmp/data.bin"

out=$(./target/release/{{ npm_name }} "$tmp/data.bin")
echo "$out" | grep -q '41 42'

out=$(printf 'AB' | ./target/release/{{ npm_name }})
echo "$out" | grep -q '41 42'

out=$(./target/release/{{ npm_name }} -w 8 "$tmp/data.bin")
echo "$out" | grep -q '41 42'

if ./target/release/{{ npm_name }} "$tmp/missing.bin" >/dev/null 2>&1; then
  echo "expected failure" >&2
  exit 1
fi

./target/release/{{ npm_name }} --help >/dev/null

echo "smoke: PASS"

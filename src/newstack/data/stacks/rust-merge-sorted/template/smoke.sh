#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-merge-sorted"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf '1\n4\n9\n' > "$tmp/a.txt"
printf '2\n3\n10\n' > "$tmp/b.txt"

out=$(./target/release/{{ npm_name }} "$tmp/a.txt" "$tmp/b.txt")
expected=$(printf '1\n2\n3\n4\n9\n10')
[ "$out" = "$expected" ] || { echo "merge mismatch: $out"; exit 1; }

printf 'oops\n' > "$tmp/bad.txt"
if ./target/release/{{ npm_name }} "$tmp/bad.txt" 2>/dev/null; then
  echo "expected a failure for a non-integer line"
  exit 1
fi

echo "smoke: PASS"

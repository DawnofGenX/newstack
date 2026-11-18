#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-jsonpath-cli"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf '{"a":{"b":1,"c":"x"},"d":[10,20],"items":[{"name":"a"},{"name":"b"}]}' > "$tmp/data.json"

out=$(./target/release/{{ npm_name }} "$tmp/data.json" '$.a.b')
test "$out" = "1"

out=$(./target/release/{{ npm_name }} "$tmp/data.json" '$.items[*].name')
test "$out" = '["a","b"]'

out=$(./target/release/{{ npm_name }} "$tmp/data.json" '$[-1]' 2>/dev/null || true)
# top-level is object; negative index should fail
./target/release/{{ npm_name }} "$tmp/data.json" '$.d[-1]' | grep -qx '20'

printf '{"a":1}' > "$tmp/missing.json"
if ./target/release/{{ npm_name }} "$tmp/missing.json" '$.b' >/dev/null 2>&1; then
  echo "expected failure" >&2
  exit 1
fi

echo "smoke: PASS"

#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-semver-cli"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

./target/release/{{ npm_name }} parse 1.2.3 >/dev/null
./target/release/{{ npm_name }} compare 1.0.0 2.0.0 >/dev/null
./target/release/{{ npm_name }} bump 1.2.3 patch | grep -qx '1.2.4'

echo "smoke: PASS"

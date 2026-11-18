#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-lru-cache"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build

echo "smoke: PASS"

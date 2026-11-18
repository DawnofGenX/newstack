#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-ring-buffer"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

echo "smoke: PASS"

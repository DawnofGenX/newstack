#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-sudoku-solver"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

puzzle=530070000600195000098000060800060003400803001700020006060000280000419005000080079
solution=534678912672195348198342567859761423426853791713924856961537284287419635345286179

out=$(./target/release/{{ npm_name }} --grid "$puzzle" | tr -d ' \n')
test "$out" = "$solution"

test "$(./target/release/{{ npm_name }} --grid "$puzzle" --count)" = "1"
test "$(./target/release/{{ npm_name }} --grid "$puzzle" --candidates 2)" = "1 2 4"
./target/release/{{ npm_name }} --help >/dev/null

echo "smoke: PASS"

#!/usr/bin/env bash
set -euo pipefail

echo "smoke: rust-s-expr"

cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test
cargo build --release

bin="target/release/{{ npm_name }}"

test "$("$bin" '(+ 1 2 3)')" = "6"
test "$("$bin" '(if (< 1 2) (list 1 2) nil)')" = "(1 2)"
test "$(printf '(len "abc")' | "$bin")" = "3"

if "$bin" '(/ 1 0)' >/dev/null 2>&1; then
  echo "smoke: division by zero must exit 1" >&2
  exit 1
fi
if "$bin" --bogus >/dev/null 2>&1; then
  echo "smoke: an unknown option must exit 2" >&2
  exit 1
fi

echo "smoke: ok"

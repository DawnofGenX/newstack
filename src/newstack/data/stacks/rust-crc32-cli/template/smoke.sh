#!/usr/bin/env bash
set -euo pipefail

echo "smoke: {{ npm_name }}"

cargo build --release
bin="target/release/{{ npm_name }}"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
printf '123456789' > "$tmp/payload.bin"

out=$("$bin" "$tmp/payload.bin")
echo "$out"
echo "$out" | grep -q "^cbf43926 $tmp/payload.bin$"

printf '123456789' | "$bin" | grep -q '^cbf43926$'
printf '123456789' | "$bin" --crc32c | grep -q '^e3069283$'
"$bin" --help | grep -q 'usage:'
if "$bin" --bogus >/dev/null 2>&1; then
  echo "expected exit 2 for --bogus" >&2
  exit 1
fi
if "$bin" "$tmp/missing.bin" >/dev/null 2>&1; then
  echo "expected exit 1 for a missing file" >&2
  exit 1
fi

echo "smoke: ok"

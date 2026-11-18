#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "smoke: kotlin-base32-cli"

gradle test --quiet

out=$(gradle run --quiet --args="encode foobar" 2>&1)
echo "$out"
test "$out" = "MZXW6YTBOI======"

back=$(gradle run --quiet --args="decode MZXW6YTBOI======" 2>&1)
test "$back" = "foobar"

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
printf '68656c6c6f' > "$tmp"
hexed=$(gradle run --quiet --args="encode --hex --file $tmp")
test "$hexed" = "NBSWY3DP"

hexback=$(gradle run --quiet --args="decode --hex --file $tmp" 2>/dev/null || true)
printf 'NBSWY3DP' > "$tmp"
hexback=$(gradle run --quiet --args="decode --hex --file $tmp")
test "$hexback" = "68656c6c6f"

echo "smoke: PASS"

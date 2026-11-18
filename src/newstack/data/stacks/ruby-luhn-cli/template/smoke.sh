#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

BIN="bin/{{ npm_name }}"
chmod +x "$BIN"

out="$("$BIN" validate 4111111111111111)"
test "$out" = "valid"

out="$("$BIN" generate 411111111111111)"
test "$out" = "4111111111111111"

out="$("$BIN" brand 4111111111111111)"
test "$out" = "visa"

echo "smoke ok"

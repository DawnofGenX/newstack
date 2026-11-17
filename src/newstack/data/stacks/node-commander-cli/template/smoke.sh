#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")" && pwd)
BIN="node $ROOT/src/cli.js"

$BIN --version | grep -q "0.1.0" || { echo "FAIL version"; exit 1; }
$BIN greet Alice | grep -q "Hello, Alice!" || { echo "FAIL greet"; exit 1; }
$BIN add 4 7 | grep -q "11" || { echo "FAIL add"; exit 1; }
echo "smoke: all checks passed"
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
printf '# Title\n\nTrailing   \n' > "$TMP/bad.md"
if node src/cli.js "$TMP/bad.md"; then
  echo "expected failure on bad markdown" >&2
  exit 1
fi
printf '# Title\n\nClean paragraph.\n' > "$TMP/good.md"
node src/cli.js "$TMP/good.md"
echo "smoke ok"

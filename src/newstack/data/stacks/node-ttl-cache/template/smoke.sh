#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-ttl-cache"

npm test

tmp=$(mktemp -d)
cat > "$tmp/ops.txt" <<'OPS'
# a value that survives, one that expires, one that is evicted
SET a 1
SET b 2 100
GET a
ADVANCE 100
GET b
STATS
OPS

out=$(node src/cli.js --capacity 4 < "$tmp/ops.txt")
grep -qx 'OK' <<<"$out"
grep -qx '(nil)' <<<"$out"
grep -q 'expirations=1' <<<"$out"

node src/cli.js --help | grep -q '^usage: '
if node src/cli.js --capacity 4 --bogus >/dev/null 2>&1; then
  echo "smoke: --bogus should exit 2" >&2
  exit 1
fi

rm -rf "$tmp"
echo "smoke: ok"

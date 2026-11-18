#!/bin/sh
set -eu
tmp=$(mktemp -d)
printf 'a\nb\n' > "$tmp/a.txt"
printf 'a\nc\n' > "$tmp/b.txt"
node src/cli.js "$tmp/a.txt" "$tmp/b.txt" | grep -q '^@@'
node src/cli.js "$tmp/a.txt" "$tmp/b.txt" --stat | grep -q 'insertions'
# apply mode
node src/cli.js "$tmp/a.txt" "$tmp/b.txt" > "$tmp/change.patch"
cp "$tmp/a.txt" "$tmp/target.txt"
node src/cli.js --apply "$tmp/change.patch" "$tmp/target.txt"
grep -q '^c$' "$tmp/target.txt"
echo ok

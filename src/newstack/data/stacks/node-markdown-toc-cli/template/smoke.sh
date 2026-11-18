#!/bin/sh
set -eu
tmp=$(mktemp -d)
cat > "$tmp/in.md" <<'EOF'
# Title

## Section One

text

### Sub

```js
# not a heading
```

Another
-------
EOF
node src/cli.js "$tmp/in.md" | grep -q "Title"
node src/cli.js "$tmp/in.md" --write
grep -q "Title" "$tmp/in.md"
grep -q "tocstop" "$tmp/in.md"
echo ok

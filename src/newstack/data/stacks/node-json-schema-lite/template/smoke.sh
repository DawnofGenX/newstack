#!/usr/bin/env bash
set -euo pipefail

echo "smoke: node-json-schema-lite"

npm test

tmp=$(mktemp -d)
cat > "$tmp/schema.json" <<'JSON'
{
  "type": "object",
  "required": ["name", "port"],
  "additionalProperties": false,
  "properties": {
    "name": { "type": "string", "minLength": 2 },
    "port": { "type": "integer", "minimum": 1, "maximum": 65535 }
  }
}
JSON

echo '{"name":"svc","port":8080}' > "$tmp/good.json"
out=$(node src/cli.js --schema "$tmp/schema.json" --data "$tmp/good.json")
grep -qx 'valid' <<<"$out"

echo '{"name":"s","port":0,"extra":1}' > "$tmp/bad.json"
if node src/cli.js --schema "$tmp/schema.json" --data "$tmp/bad.json" 2> "$tmp/err.txt"; then
  echo "smoke: an invalid document must exit 1" >&2
  exit 1
fi
grep -q '^\$.name: must be at least 2 characters$' "$tmp/err.txt"
grep -q '^\$.port: must be >= 1$' "$tmp/err.txt"
grep -q '^\$.extra: is not an allowed property$' "$tmp/err.txt"

node src/cli.js --help | grep -q '^usage: '
if node src/cli.js --bogus >/dev/null 2>&1; then
  echo "smoke: --bogus should exit 2" >&2
  exit 1
fi

rm -rf "$tmp"
echo "smoke: ok"

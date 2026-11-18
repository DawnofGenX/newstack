#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-template-cli"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

tmp=$(mktemp -d)
cat > "$tmp/conf.tmpl" <<'TPL'
server {{! .server.host }}:{{! .server.port }}
{{! range .upstreams }}- {{! upper . }}
{{! end }}
TPL
echo '{"server":{"host":"127.0.0.1","port":8080},"upstreams":["api","db"]}' > "$tmp/data.json"

out=$(./bin/{{ npm_name }} -template "$tmp/conf.tmpl" -data "$tmp/data.json")
grep -q 'server 127.0.0.1:8080' <<<"$out"
grep -q -- '- API' <<<"$out"

./bin/{{ npm_name }} -template "$tmp/conf.tmpl" -data "$tmp/data.json" -out "$tmp/rendered.txt"
grep -q -- '- DB' "$tmp/rendered.txt"

echo '{}' > "$tmp/empty.json"
if ./bin/{{ npm_name }} -template "$tmp/conf.tmpl" -data "$tmp/empty.json" >/dev/null 2>&1; then
  echo "smoke: a missing key must fail" >&2
  exit 1
fi
if ./bin/{{ npm_name }} -bogus >/dev/null 2>&1; then
  echo "smoke: an unknown flag must exit 2" >&2
  exit 1
fi

rm -rf "$tmp"
echo "smoke: ok"

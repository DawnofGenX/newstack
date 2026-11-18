#!/usr/bin/env bash
set -euo pipefail

echo "smoke: go-sitemap-cli"

go vet ./...
go test ./...
go build -o bin/{{ npm_name }} .

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

cat > "$tmp/sitemap.xml" <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://example.com/docs</loc>
  </url>
</urlset>
XML

out=$(bin/{{ npm_name }} -file "$tmp/sitemap.xml")
echo "$out"
test "$out" = "urls=2"

bin/{{ npm_name }} -file "$tmp/sitemap.xml" -render | grep -qF '<changefreq>daily</changefreq>'
bin/{{ npm_name }} -file "$tmp/sitemap.xml" -render | grep -q 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'

printf '<urlset><url><loc>relative/path</loc></url></urlset>' > "$tmp/bad.xml"
set +e
bin/{{ npm_name }} -file "$tmp/bad.xml" > /dev/null 2>"$tmp/err.txt"
code=$?
set -e
test "$code" -eq 1
grep -q 'absolute http(s) URL' "$tmp/err.txt"

set +e
bin/{{ npm_name }} --bogus > /dev/null 2>&1
code=$?
set -e
test "$code" -eq 2

echo "smoke: ok"

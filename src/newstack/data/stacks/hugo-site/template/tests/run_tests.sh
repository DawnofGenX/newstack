#!/bin/sh
# Dependency-free assertions over the generated site. Hugo renders into a
# temporary directory, so the suite never reads a stale public/ tree.
set -u

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp=$(mktemp -d)
broken="$root/content/zz-broken.md"
cleanup() {
	rm -rf "$tmp"
	rm -f "$broken"
}
trap cleanup EXIT INT TERM

passed=0
failed=0

pass() { passed=$((passed + 1)); }
fail() { failed=$((failed + 1)); printf 'FAIL %s\n' "$1"; }

file_has() { # file_has <path> <text> <name>
	if [ ! -f "$1" ]; then
		fail "$3 (missing $1)"
	elif grep -qF -- "$2" "$1"; then
		pass
	else
		fail "$3"
	fi
}

file_lacks() { # file_lacks <path> <text> <name>
	if [ ! -f "$1" ]; then
		fail "$3 (missing $1)"
	elif grep -qF -- "$2" "$1"; then
		fail "$3"
	else
		pass
	fi
}

file_exists() {
	if [ -f "$1" ]; then pass; else fail "$2 (missing $1)"; fi
}

cd "$root" || exit 1
site="$tmp/public"

if hugo --quiet --destination "$site" > "$tmp/build.log" 2>&1; then
	pass
else
	fail "hugo build"
	cat "$tmp/build.log"
	printf 'checks: %d, passed: %d, failed: %d\n' $((passed + failed)) "$passed" "$failed"
	exit 1
fi

home="$site/index.html"
post="$site/posts/welcome/index.html"

file_exists "$home" "home page rendered"
file_exists "$post" "post page rendered"
file_exists "$site/about/index.html" "about page rendered"
file_exists "$site/posts/index.html" "section list rendered"
file_exists "$site/404.html" "404 page rendered"
file_exists "$site/sitemap.xml" "sitemap written"
file_exists "$site/index.xml" "RSS feed written"
file_exists "$site/robots.txt" "robots.txt written"

file_has "$home" "<!doctype html>" "home page is html"
file_has "$home" "class=\"post-list\"" "home page lists posts"
file_has "$home" "/posts/welcome/" "home page links the post"
file_has "$post" "The first post on a brand new site." "post description reaches the meta tag"
file_has "$home" "class=\"site-header\"" "header partial rendered"
file_has "$home" "class=\"site-footer\"" "footer partial rendered"
file_has "$home" "lang=\"en-us\"" "language code rendered"
if grep -qE '<meta name="description" content="[^"]+"' "$home"; then pass; else fail "home page has a meta description"; fi

file_has "$post" "<aside class=\"note\">" "note shortcode rendered"
file_has "$post" "id=\"what-to-change-first\"" "markdown headings get ids"
file_has "$post" "15 January 2026" "date formatted by the layout"
file_has "$site/posts/index.html" "Welcome" "section list contains the post"
file_has "$site/sitemap.xml" "<urlset" "sitemap is a urlset"
file_has "$site/index.xml" "<rss" "feed is rss"
file_has "$site/robots.txt" "Sitemap:" "robots.txt points at the sitemap"

file_lacks "$home" "{{<" "no unrendered shortcode left in the output"
file_lacks "$home" "livereload.js" "no development script in a built page"
file_lacks "$post" "draft = true" "front matter is not echoed into the page"

css=$(grep -o 'href="/css/main\.min\.[0-9a-f]\{64\}\.css"' "$home" | head -1)
if [ -n "$css" ]; then pass; else fail "stylesheet is fingerprinted"; fi
file_exists "$site"/css/main.min.*.css "stylesheet written"

# A malformed front matter must stop the build: rendering whatever parses is not
# the same as failing loudly.
printf '+++\ntitle = \n+++\n' > "$broken"
if hugo --quiet --destination "$tmp/broken" > "$tmp/broken.log" 2>&1; then
	fail "bad front matter is rejected"
else
	pass
fi
rm -f "$broken"

printf 'checks: %d, passed: %d, failed: %d\n' $((passed + failed)) "$passed" "$failed"
[ "$failed" -eq 0 ]

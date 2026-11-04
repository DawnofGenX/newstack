# {{ title }}

{{ description }}

A [Hugo](https://gohugo.io/) site with a hand-written layout, no theme and no
JavaScript. Markdown under `content/` is rendered into `public/` by a single
`hugo` invocation.

## Getting started

```console
$ make build       # render the site into public/
$ make serve       # http://localhost:1313, with live reload
$ make test        # render into a temp dir and assert on the output
```

`hugo` is the only requirement. `make` just wraps it so the commands are the same
on every machine.

## Layout

```
hugo.toml              site title, base URL, params, markup options
content/               pages and posts, each with TOML front matter
layouts/baseof.html    the html shell every page is rendered into
layouts/home.html      the home page (the post list)
layouts/page.html      one page or post
layouts/section.html   a section list, e.g. /posts/
layouts/partials/      head, header and footer fragments
layouts/shortcodes/    the {{< note >}} block used in the sample post
assets/css/main.css    minified and fingerprinted at build time
static/                files copied verbatim, like favicon.svg
tests/run_tests.sh     the assertions `make test` runs
```

`assets/` and `static/` are not the same thing: anything under `assets/` is
processed by Hugo's pipeline (here the CSS is minified and fingerprinted, and the
resulting `<link>` carries a subresource-integrity hash), while `static/` is
copied byte for byte.

## Checks

`make test` renders the whole site into a temporary directory and asserts on the
HTML: the partials ran, the shortcode expanded, headings got ids, the stylesheet
is fingerprinted, the sitemap and RSS feed exist, robots.txt points at the
sitemap, and no development-only script leaked into a built page. It also writes
a deliberately malformed front matter and requires the build to *fail*, so a
broken page cannot pass silently.

## Adding a post

```console
$ hugo new content posts/second-post.md
```

Or copy `content/posts/welcome.md` and change the front matter. The `draft = true`
line keeps a page out of a normal build until you flip it; `hugo --buildDrafts`
renders drafts locally.

## Changing the look

Edit `assets/css/main.css` and the fragments in `layouts/partials/`. Hugo rebuilds
in milliseconds, and `make serve` reloads the browser for you.

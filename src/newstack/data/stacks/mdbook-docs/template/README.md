# {{ npm_name }}

A book built with [mdBook](https://rust-lang.github.io/mdBook/), plus the one
thing most documentation projects skip: **links are checked in CI**, and so is
the summary.

```sh
make build     # render the site into book/
make check     # relative links resolve; every page is listed in src/SUMMARY.md
make test      # 25 assertions over the checker
make serve     # live preview
```

## Layout

```
book.toml             mdBook configuration (title, author, build dir)
src/SUMMARY.md        the table of contents — the sidebar, and the page list
src/index.md          introduction
src/guide/*.md        how to write a page, how the checker works
src/reference/*.md    the command line
tools/check-links.sh  the checker: 0 intact, 1 broken, 2 usage error
tests/                harness.sh, check_links_test.sh, run_tests.sh
```

## What the checker does

`tools/check-links.sh [ROOT]` reads every markdown file under `src/` and asks:

1. Does every relative link and image point at a file that exists?
2. Is every page reachable from `src/SUMMARY.md`?

Both failures are reported with a file and (for a link) a line number, and the
exit status is 1. External links, `mailto:` links and bare `#anchors` are left
alone: they need the network, or they refer to the page they are on.

```
$ ./tools/check-links.sh
src/guide/writing.md:5: nowhere.md does not exist
src/orphan.md: not listed in src/SUMMARY.md
checked 6 file(s), 9 link(s): 2 problem(s)
```

Reference-style links (`[text]: target`) are deliberately not resolved — this
book does not use them, and guessing would be worse than saying so.

## Adding a page

1. Write `src/guide/new-page.md`.
2. Link it from `src/SUMMARY.md` — otherwise the checker reports it as an
   orphan, which is exactly what a reader would have found: a page nobody can
   navigate to.
3. `make check`, then `make build`.

## Requirements

`mdbook` 0.4 or newer on `PATH` for `make build` and `make serve`. The checker
and its tests need only `bash` and `make`.

## License

MIT — see `LICENSE`.

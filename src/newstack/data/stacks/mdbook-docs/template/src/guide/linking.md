# Check every link

`tools/check-links.sh` reads every markdown file under `src/` and asks two
questions:

1. Does every relative link and image point at a file that exists?
2. Is every page reachable from `src/SUMMARY.md`?

External links, `mailto:` links and bare anchors (`#section`) are left alone:
they need the network, or they refer to the page they are on.

```sh
make check      # same as tools/check-links.sh
```

The exit status is part of the contract: `0` when the book is intact, `1` when
something is broken, `2` for a usage error. The tests in `tests/` cover each of
those, including a broken link, a missing image, an orphan page and a link with
an anchor.

## Why bother

A dead link is invisible in review and obvious to a reader. Checking them in CI
costs seconds and makes "the docs are wrong" a build failure instead of a bug
report.

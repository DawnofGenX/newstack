# Write a page

A page is a markdown file under `src/`. Add it to `src/SUMMARY.md` and it shows
up in the sidebar; a page that is not in the summary is reported by
`tools/check-links.sh` and fails the build in CI.

## Structure

- One `#` heading per page: that is what the sidebar and the anchors use.
- Link to another page with a relative path: [the introduction](../index.md).
- Link to a heading with an anchor: [the reference](../reference/cli.md#commands).

## Preview

```sh
make serve
```

The book rebuilds as you save. `make build` writes the static site to `book/`,
which is ignored by git.

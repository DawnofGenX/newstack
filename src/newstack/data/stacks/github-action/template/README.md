# {{ title }}

{{ description }}

A JavaScript GitHub Action with zero runtime dependencies: `src/count.js` is pure
counting, `src/report.js` turns rows into a Markdown table, and `src/index.js` is a
thin wrapper that reads `INPUT_*` and appends to `GITHUB_STEP_SUMMARY` and
`GITHUB_OUTPUT`.

## Usage

```yaml
- uses: ./
  id: measure
  with:
    paths: README.md, src/index.js
    title: Bundle size
- run: echo "total bytes ${{! steps.measure.outputs.bytes }}"
```

Inputs: `paths` (required, comma or newline separated), `title` (summary heading).
Outputs: `lines`, `words`, `bytes` — totals across every file, counted the way `wc`
counts (newlines, whitespace-separated words, UTF-8 bytes).

## Layout

```
action.yml                  inputs, outputs, `runs: using: node24`
src/count.js                pure counting
src/report.js               path parsing, file reads, Markdown table
src/index.js                environment in, summary and outputs out
test/                       node:test — pure functions plus a real child-process run
.github/workflows/ci.yml    syntax check, tests, then `uses: ./` on this repo
```

## Test

```console
$ npm test
$ npm run check
```

`npm test` runs `node --test`; there is nothing to install, because the action has no
dependencies. The entry-point test spawns `src/index.js` with a temporary workspace and
temp `GITHUB_OUTPUT` / `GITHUB_STEP_SUMMARY` files, then asserts on what was written.

## License

MIT — see [LICENSE](LICENSE).

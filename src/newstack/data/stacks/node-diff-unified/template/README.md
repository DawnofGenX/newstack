# {{ title }}

{{ description }}

## Usage

```sh
node src/cli.js old.txt new.txt
npm test
```

`diffLines` walks a longest-common-subsequence table and emits ` `/`-`/`+` operations with
both line numbers, `hunks` groups changes that are within `context` lines of each other, and
`unifiedDiff` renders standard `---`/`+++`/`@@` output. Identical files print `identical`
instead of an empty diff, which keeps the smoke test honest.

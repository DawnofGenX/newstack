# {{ title }}

{{ description }}

## Usage

```sh
deno task test

diff old.txt new.txt              # unified diff, three lines of context
diff -U 0 old.txt new.txt         # no context lines
diff --stat old.txt new.txt       # counts only
diff --exit-code a.txt b.txt      # exit 1 when they differ
diff -q a.txt b.txt               # print nothing at all
cat new.txt | diff - old.txt      # "-" reads stdin
```

The edit script comes from a longest-common-subsequence table, so a moved
block shows up as one deletion plus one addition rather than a rewrite of
everything after it. Hunks merge when two changes sit within `2*context`
lines. Exit codes: 0 success, 1 a file could not be read, 2 bad usage.

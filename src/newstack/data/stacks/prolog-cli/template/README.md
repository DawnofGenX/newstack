# {{ title }}

{{ description }}

A `wc`-style line, word and byte counter written in SWI-Prolog with no
dependencies outside the standard library.

## Layout

```
main.pl                 entry point: real streams, real exit status
lib/counts.pl           byte-exact counting over a stream
lib/options.pl          hand-rolled argv parser
lib/runner.pl           rows, totals, exit codes (output behind two closures)
tests/run_tests.pl      runs every suite and exits non-zero on a failure
bin/{{ npm_name }}      wrapper that resolves the project root and calls swipl
```

## Run it

```console
$ printf 'alpha beta\ngamma delta\n' > sample.txt
$ ./bin/{{ npm_name }} sample.txt
 2  4 23 sample.txt
$ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
3 -
$ ./bin/{{ npm_name }} --version
0.1.0
```

Exit codes follow `wc`'s contract: `0` when every file was read, `1` when a
file could not be opened, `2` for a usage error.

## Tests

```console
$ swipl -q -f tests/run_tests.pl
checks: 58, passed: 58, failed: 0
```

The suite is a four-predicate harness (`check/2`, `check_eq/3`, a tally and a
report) rather than a framework: it counts assertions, prints only failures and
exits non-zero when the tally is not clean.

## Why the counting lives in `lib/`

`lib/counts.pl` only knows how to turn a stream into a tally, and
`lib/runner.pl` only knows how to turn arguments plus a tally into rows and an
exit code — the two writers it takes as arguments are how the tests see the
output without touching the process's own streams. `main.pl` is the single file
that opens `/dev/stdin`, writes to the real streams and calls `halt/1`.

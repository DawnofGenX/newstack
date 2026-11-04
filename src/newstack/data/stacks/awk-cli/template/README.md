# {{ npm_name }}

A byte-accurate `wc`-style counter written in `awk`. No dependencies beyond
`gawk`.

```console
$ printf 'alpha beta\ngamma delta\n' > sample.txt
$ ./bin/{{ npm_name }} sample.txt
 2  4 23 sample.txt
$ ./bin/{{ npm_name }} -w sample.txt
4 sample.txt
$ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
3
```

The figures, the padding and the `total` row are byte-identical to
`wc -l -w -c`, including the odd cases: a pipe is padded to seven columns, a
single figure over a single operand is not padded at all, and a `total` row
appears as soon as there is more than one operand even when one of them could
not be read.

## Why `RS = "\0"`

`awk` normally splits input into lines, which throws away the information you
need to count exactly (`wc` counts a final line without a newline). Setting the
record separator to a NUL byte makes each file a single record:

- bytes — `length(data)` under `LC_ALL=C`
- lines — `gsub(/\n/, "&", copy)`
- words — `gsub(/[^ \t\n\r\v\f]+/, "&", copy)`

The wrapper exports `LC_ALL=C` for that reason; without it `length()` counts
characters instead of bytes.

## Layout

```
main.awk              the only file that runs: sets RS, exits with the code
lib/counts.awk        counts_of() — the byte-level counting
lib/options.awk       options_parse() — flags, clusters, `--`, `-`
lib/runner.awk        report_build() — reading, padding, totals, messages
tests/harness.awk     check / check_int / check_text / report
tests/run_tests.awk   the whole suite, in one process
bin/{{ npm_name }}         the wrapper: finds its root, sets the locale
```

`lib/runner.awk` never prints anything itself: it fills `OUT_TEXT`, `ERR_TEXT`
and `EXIT_CODE`, and `main.awk` prints them once. That is what lets the suite
drive the entire CLI in-process — 69 checks, no subprocesses:

```console
$ LC_ALL=C gawk -f lib/counts.awk -f lib/options.awk -f lib/runner.awk \
      -f tests/harness.awk -f tests/run_tests.awk
checks: 69, passed: 69, failed: 0
```

The one thing the suite cannot see is the real standard input, because `awk`
has no way to swap its own stdin for a string. The `stdin` step in
`stack.json` and in CI covers that against the built wrapper, which is how the
"No FILE" path stays honest.

## Exit codes

| code | meaning |
| --- | --- |
| 0 | every operand was read |
| 1 | at least one operand could not be opened |
| 2 | the arguments were not understood |

## Licence

MIT — see `LICENSE`.

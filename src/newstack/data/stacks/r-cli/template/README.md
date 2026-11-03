# {{ title }}

{{ description }}

A minimal base-R command line tool: counting lives in `R/counts.R` (pure
functions, no I/O) so tests drive it directly, parsing lives in `R/options.R`,
and `bin/{{ npm_name }}` is the thin entry point that owns argv, stdout/stderr
and the exit code.

## Layout

```
bin/{{ npm_name }}             entry point: argv -> help | usage | count, plus quit(status)
R/counts.R                     textstat_counts(): lines, words, bytes — pure, no I/O
R/options.R                    textstat_parse_args(): argv -> options list — pure, no I/O
tests/harness.R                hand-rolled expect_equal/describe/it, no dependencies
tests/run.R                    runner: Rscript tests/run.R
tests/counts_test.R            counting edge cases
tests/options_test.R           every parser branch
tests/cli_test.R               the real script: stdout and exit codes
DESCRIPTION                    package manifest: name, version, author, license
```

No dependencies: only base R, no CRAN packages and no network.

## Requirements

R, whose interpreter is `Rscript`. On Debian or Ubuntu:

```console
$ sudo apt-get install -y r-base-core
```

## Run

```console
$ Rscript bin/{{ npm_name }} --help
$ Rscript bin/{{ npm_name }} README.md
$ cat README.md | Rscript bin/{{ npm_name }} -w
```

The script locates its own `R/` directory from the `--file=` argument Rscript
passes, so it works from any directory, not just the project root.

Output is wc-style, right-aligned: lines, words, bytes, then the path.

```
       3        5       30 sample.txt
```

## Line, word and byte semantics

`lines` is the number of `\n` bytes, `words` is the number of maximal
non-whitespace runs, and `bytes` is the raw length. A file that ends without a
trailing newline therefore reports one fewer line than it has visual lines, which
is exactly what `wc -l` does. The suite pins this down:

```console
$ printf 'hello' | Rscript bin/{{ npm_name }}   # 0 lines, 1 word, 5 bytes
$ printf 'hello\n' | Rscript bin/{{ npm_name }}  # 1 line, 1 word, 6 bytes
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0    | success, including `--help` and `--version` |
| 1    | a file could not be read |
| 2    | usage error: unknown flag, conflicting modes |

## Test

```console
$ Rscript tests/run.R
```

The runner prints one `ok` line per test, keeps going past a failure, and ends
with `N passed, M failed`. Exit status is 0 only when every test passed.
`tests/cli_test.R` spawns `bin/{{ npm_name }}` through `system()`, so the exit
codes are the ones a shell would see.

## Package identity

newstack renders a lowercase `package_name` with underscores ({{ package_name }})
for languages that need it as an identifier. R identifiers cannot contain
hyphens, so the dashed `{{ npm_name }}` form names the binary (`bin/{{ npm_name }}`)
while the underscored `{{ package_name }}` form names the package in
`DESCRIPTION`.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.

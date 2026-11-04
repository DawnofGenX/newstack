# {{ title }}

{{ description }}

A minimal Clojure command line tool built on the **Clojure CLI** tooling
(`deps.edn` + `clj`/`clojure`): there is no Leiningen, no Maven, no build
daemon. `deps.edn` declares the one runtime dependency — the Clojure runtime
itself — and a `:test` alias that adds the `test/` directory to the classpath.

The code is split the way the other newstack CLIs are: counting is pure and
knows nothing about I/O (`src/textstat/counts.clj`), parsing turns `argv` into
a decision (`options.clj`), `cli.clj` turns that decision into output and an
exit code against a record of callbacks, and `main.clj` is the only file that
touches the real process — `System/in`, `Files/readAllBytes` and `System/exit`.

## Layout

```
deps.edn                                     Clojure CLI build: one dep, a :test alias
bin/{{ npm_name }}                           wrapper: `clojure -M -m textstat.main "$@"`
src/textstat/counts.clj                      of-bytes(bytes) and the aligned row layout — pure
src/textstat/options.clj                     parse(argv): figures/files/status — pure
src/textstat/cli.clj                         run(argv, io): Int, the exit-code contract
src/textstat/main.clj                        the real io: stdin/stdout/stderr and System/exit
test/textstat/counts_test.clj                wc semantics: trailing newline, whitespace runs, UTF-8 bytes
test/textstat/options_test.clj               every parser branch: clusters, `--`, `-`, help, errors
test/textstat/cli_test.clj                   exit codes and layout, asserted against a fake io
test/textstat/run_tests.clj                  runs the suite and exits non-zero on failure
```

`cli/run` takes an `io` record of callbacks rather than reading the world
directly, so the exit contract — and the exact spacing of the output — is
tested without spawning a process or touching the filesystem.

## Requirements

A JDK (21 here, installed through `actions/setup-java` in CI) and the
**Clojure CLI** 1.12.6. The runtime is fetched from Maven Central on the first
`clojure` run and cached under `~/.m2`; after that builds and tests are
offline.

## Build

There is no separate compile step — Clojure is compiled on load. To prove the
namespaces load and compile:

```console
$ clojure -M -e "(require 'textstat.cli)"
```

## Test

```console
$ clojure -M:test -m textstat.run-tests
```

Three `clojure.test` suites, no custom framework: `counts_test` pins the `wc`
semantics, `options_test` covers every branch of the parser, and `cli_test`
asserts the 0/1/2 exit contract and the column layout through a fake `io`.
`run_tests` runs all three and exits non-zero if any test fails, so the gate
and CI can rely on the process status.

## Run

```console
$ ./bin/{{ npm_name }} --help
$ ./bin/{{ npm_name }} README.md
$ cat README.md | ./bin/{{ npm_name }} -w
```

Output is `wc`-style: lines, words, bytes, then the path. Every column is
right-aligned to the widest figure in the output, and with more than one file a
`total` line is printed.

```console
$ printf 'alpha beta\ngamma\n' > sample.txt
$ ./bin/{{ npm_name }} sample.txt
 2  3 17 sample.txt
```

`-l`, `-w` and `-c` combine in any order (and cluster, as in `-lw`); with no
counting flag all three figures are printed. Lines follow `wc -l`: they count
`\n` bytes, so a last line without a trailing newline is not counted. Bytes are
raw bytes, so `héllo wörld` is 13 bytes, not 11.

The wrapper runs the project in place, so the first invocation after a clean
checkout compiles and prints the Clojure CLI's progress on stderr.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0    | success, including `--help` and `--version` |
| 1    | a file could not be read (the other files are still counted) |
| 2    | usage error: unknown option |

`cli/run` *returns* these codes; only `main` calls `System/exit`, which is what
lets `cli_test` assert them directly.

## Naming

The package is `textstat` and the command is `bin/{{ npm_name }}`; the usage
line prints the command name from `cli/program`, so rename the wrapper and that
constant together. To rename the *package*, move `src/textstat/` and
`test/textstat/` and change the `ns textstat.…` line in each file.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.

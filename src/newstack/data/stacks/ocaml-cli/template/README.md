# {{ title }}

{{ description }}

A minimal OCaml command line tool laid out the way dune expects a project to
be: counting lives in `lib/counts.ml` (pure functions, no I/O), parsing lives
in `lib/options.ml`, `lib/runner.ml` turns a parsed command line into output
and an exit code, and `bin/main.ml` is the thin entry point that owns
`Sys.argv`, the standard streams and `exit`.

## Layout

```
dune-project                 dune manifest: (lang dune 3.14)
lib/dune                     library manifest: the `textstat` library
lib/counts.ml                Counts.of_bytes(data): lines, words, bytes — pure, no I/O
lib/options.ml               Options.parse(argv): figures/files/status — pure, no I/O
lib/runner.ml                Runner.run(args, stdin, stdout, stderr) : int — the exit-code contract
bin/dune                     executable manifest: `main`, links `textstat`
bin/main.ml                  entry point: hands argv and the streams to Runner, exits
bin/{{ npm_name }}           shell wrapper: `exec dune exec main -- "$@"`
test/dune                    test manifest: a `test_harness` library + three test executables
test/harness.ml              check/check_eq/finish — pass/fail tally, non-zero exit on failure
test/counts_test.ml          wc semantics: trailing newline, whitespace, UTF-8 bytes
test/options_test.ml         every parser branch: flags, `--`, `-`, help, errors
test/runner_test.ml          the exit-code contract, asserted without spawning
```

The library is declared `(wrapped false)`, so its modules are `Counts`, `Options`
and `Runner` rather than `Textstat.Counts`: dune's default wrapping would force
an `open` in every consumer, including the tests. The executable is `dune`'s
`main` (an executable name must be a valid module identifier, so it cannot carry
the dashed project name); the `bin/{{ npm_name }}` wrapper is the name users type.

No dependencies: the `textstat` library links only the OCaml standard library,
so `dune build` and `dune runtest` work offline with no opam packages.

## Requirements

OCaml 4.14 or newer and dune 3.14 or newer. The template is developed and
tested with OCaml 4.14.1 and dune 3.14.0; CI installs OCaml 4.14.1 through
`ocaml/setup-ocaml`.

## Build

```console
$ dune build @all
```

`dune build @all` builds the `textstat` library, the `main` executable and the
test executables. The user-facing entry point is the shell wrapper
`bin/{{ npm_name }}`, which forwards to the dune executable and passes the
exit code through unchanged.

## Run

```console
$ ./bin/{{ npm_name }} --help
$ ./bin/{{ npm_name }} README.md
$ cat README.md | ./bin/{{ npm_name }} -w
```

Output is `wc`-style: lines, words, bytes, then the path. Every figure is
right-aligned to the width of the widest figure printed, the way `wc` lines up
columns.

```console
$ printf 'alpha beta\ngamma\n' > sample.txt
$ ./bin/{{ npm_name }} sample.txt
 2  3 17 sample.txt
```

The counting flags combine like `wc`: `-l`, `-w` and `-c` may be given in any
order, and with no counting flag all three figures are printed. Lines follow
`wc -l`: they count `\n` bytes, so a last line without a trailing newline is
not counted. Bytes are raw bytes, so UTF-8 text can be wider than it looks.
With more than one file a `total` line is printed.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0    | success, including `--help` and `--version` |
| 1    | a file could not be read (other files are still counted) |
| 2    | usage error: unknown flag |

`Runner.run` *returns* these codes; only `bin/main.ml` calls `exit`, which is
what lets `test/runner_test.ml` assert them without spawning a process.

## Test

```console
$ dune runtest
```

`dune runtest` builds and runs the three test executables. They use a
hand-rolled harness (`test/harness.ml`) built on the standard library only —
no alcotest, no ounit — and print a `N passed, M failed` tally, exiting
non-zero if anything failed. Nothing needs the network.

## Package identity and renaming

The dune executable is deliberately fixed as `main` (in `bin/dune` and
`bin/main.ml`), because a dashed project name such as `{{ npm_name }}` is not
a valid OCaml module identifier and dune requires the executable's `name` to
be one. The user-facing name is the shell wrapper `bin/{{ npm_name }}`, which
runs `dune exec main -- "$@"`.

To rename the *library* (say to `wordcount`):

1. `git mv lib lib` is not needed — rename the directory if you like, but the
   dune `name` is what matters.
2. In `lib/dune`, change `(name textstat)` to `(name wordcount)`.
3. In `bin/dune` and `test/dune`, change the `textstat` library reference to
   `wordcount`.
4. In `lib/runner.ml`, the `open Counts` and the `Options`/`Counts` references
   are unaffected; only the library *name* changes.

Renaming just the *binary* is easier: change the wrapper filename
`bin/{{ npm_name }}` and the `program` value in `lib/runner.ml` together, so
the usage line still matches the command.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.

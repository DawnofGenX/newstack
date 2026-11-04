# {{ title }}

{{ description }}

A minimal Gleam command line tool laid out the way `gleam` expects a project
to be: counting lives in `src/textstat/counts.gleam` (pure functions, no I/O),
parsing lives in `src/textstat/options.gleam`, `src/textstat/runner.gleam`
turns a parsed command line into output and an exit code, and
`src/{{ package_name }}.gleam` is the thin entry point that owns argv, stdin
and the process exit code.

## Layout

```
gleam.toml                          project manifest: name, version, erlang target
src/{{ package_name }}.gleam        entry point: hands argv and stdin to Runner, halts
src/textstat_io.erl                 Erlang helper: argv and stdin from the runtime
src/textstat/counts.gleam           Counts.of_bytes(data): lines, words, bytes — pure
src/textstat/options.gleam          Options.parse(argv): figures/files/status — pure
src/textstat/runner.gleam           Runner.run(args, stdin) : Int — the exit-code contract
bin/{{ npm_name }}                  shell wrapper: `exec gleam run --no-print-progress -- "$@"`
test/harness.gleam                  check/check_eq — pass/fail tally
test/counts_test.gleam              wc semantics: trailing newline, whitespace, UTF-8 bytes
test/options_test.gleam             every parser branch: flags, `--`, `-`, help, errors
test/runner_test.gleam              the exit-code contract, asserted without spawning
test/{{ package_name }}_test.gleam  test entry point: runs every module, halts on failure
```

The Erlang helper (`src/textstat_io.erl`) exists because the Gleam standard
library (1.0.x) has no file I/O, no argv access and no way to set the process
exit code. Those come from the Erlang/OTP runtime via `@external(erlang, ...)`:
`init:get_plain_arguments/0` for argv, `io:get_line/1` for stdin,
`file:read_file/1` for files and `erlang:halt/1` for the exit code. Gleam
compiles the `.erl` file alongside the `.gleam` sources.

No third-party dependencies: the only hex package is `gleam_stdlib` (the
standard library), so `gleam build` and `gleam test` work with no other
packages. The test suite is a hand-rolled harness (`test/harness.gleam`) using
plain assertions — no gleeunit.

## Requirements

Gleam 1.19 or newer and Erlang/OTP 27 (the pair CI installs through
`erlef/setup-beam`). The template is developed and tested with Gleam 1.19.2 and
OTP 27.3.

## Build

```console
$ gleam build
```

`gleam build` compiles the `textstat` modules, the entry point and the Erlang
helper. The user-facing entry point is the shell wrapper `bin/{{ npm_name }}`,
which forwards to `gleam run` and passes the exit code through unchanged.

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
not counted. Bytes are raw bytes, so UTF-8 text can be wider than it looks
(`héllo wörld` is 13 bytes, not 11). With more than one file a `total` line is
printed.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0    | success, including `--help` and `--version` |
| 1    | a file could not be read (other files are still counted) |
| 2    | usage error: unknown flag |

`Runner.run` *returns* these codes; only `src/{{ package_name }}.gleam` calls
`erlang:halt`, which is what lets `test/runner_test.gleam` assert them without
spawning a process. `gleam run` propagates the VM exit status to the shell, so
the wrapper's exit code is the program's.

## Test

```console
$ gleam test
```

`gleam test` builds and runs the test entry point
(`test/{{ package_name }}_test.gleam`), which runs the three test modules and
prints a tally, exiting non-zero if anything failed. Nothing needs the network.

## Package identity and renaming

Three names, because Gleam's rules differ from a shell's:

- `name` in `gleam.toml` is `{{ package_name }}` — Gleam package names may only
  contain lowercase letters, digits and underscores, so the hyphenated project
  name cannot be used there.
- the entry-point module is `src/{{ package_name }}.gleam`, and the test entry
  point is `test/{{ package_name }}_test.gleam`, because a module name has to
  match its file name.
- the user-facing command is the shell wrapper `bin/{{ npm_name }}`, which runs
  `gleam run --no-print-progress -- "$@"`. `gleam run` forwards the VM exit
  status, so the wrapper's exit code is the program's.

To rename the *package*, change `name` in `gleam.toml`, the entry-point module
file `src/<name>.gleam` and the test entry point `test/<name>_test.gleam`
together. To rename just the *binary*, change the wrapper filename
`bin/{{ npm_name }}` and the `program` constant in `src/textstat/runner.gleam`
together, so the usage line still matches the command.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.

# {{ title }}

{{ description }}

A minimal Nim command line tool: counting lives in
`src/{{ package_name }}/counting.nim` (pure functions, no I/O) so tests drive it
directly, parsing lives in `src/{{ package_name }}/options.nim`, and
`src/{{ package_name }}.nim` is the thin entry point that owns argv, stdout/stderr
and the exit code.

## Layout

```
{{ package_name }}.nimble      package manifest: srcDir, bin, `nimble test` task
nim.cfg                        compiler settings for `nim`, `nimble build` and `nimble test`
src/{{ package_name }}.nim     entry point: argv → help | usage | count, plus `quit(code)`
src/{{ package_name }}/counting.nim   count(): lines, words, bytes — pure, no I/O
src/{{ package_name }}/options.nim    parseOptions(): argv → Options — pure, no I/O
tests/test_all.nim             unittest suite: counting, parsing, real exit codes
```

No dependencies: the `.nimble` file only requires `nim >= 1.6`.

## Requirements

Nim 1.6 or newer, plus nimble. The template is tested with Nim 1.6.14 locally and
with Nim 2.2.4 in CI, so it sticks to standard library modules that exist in both.

## Build

```console
$ nimble build
```

The binary is `./{{ package_name }}` in the project root.

## Run

```console
$ ./{{ package_name }} --help
$ ./{{ package_name }} README.md
$ cat README.md | ./{{ package_name }} -w
```

Output is wc-style, right-aligned: lines, words, bytes, then the path.

```
       3        5       30 sample.txt
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0    | success, including `--help` and `--version` |
| 1    | a file could not be read |
| 2    | usage error: unknown flag, conflicting modes |

## Test

```console
$ nimble test
```

The `test` task in `{{ package_name }}.nimble` compiles the binary and then runs
`tests/test_all.nim` with the standard `unittest` module. The suite covers empty
input, trailing newlines, extra whitespace, mode selection, `--` handling, and
each exit code by running the built binary through `execCmdEx`.

## Package identity

newstack renders a lowercase `package_name` with underscores, because Nim
module names and the `bin` entry of a `.nimble` file must be identifiers. The
dashed `{{ npm_name }}` form appears only in prose like this paragraph: the
binary, the module and the `.nimble` file are all `{{ package_name }}`, and
`--help` prints exactly that name so the usage line matches the command.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.

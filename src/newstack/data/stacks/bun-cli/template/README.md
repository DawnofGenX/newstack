# {{ title }}

{{ description }}

A minimal Bun command line tool: counting lives in `src/textstat/counts.ts`
(pure functions, no I/O) so tests drive it directly, parsing lives in
`src/textstat/options.ts`, and `bin/{{ npm_name }}` is the thin entry point
that owns argv, stdout/stderr and the exit code.

## Layout

```
bin/{{ npm_name }}             entry point: argv -> help | usage | count, plus process.exit(code)
src/cli.ts                      thin entry: reads files, prints wc-style output, owns the exit code
src/textstat/counts.ts          count(): lines, words, bytes — pure, no I/O
src/textstat/options.ts         parseArgs(): argv -> options — pure, no I/O
tests/counts.test.ts            counting edge cases
tests/options.test.ts           every parser branch
tests/cli.test.ts               the real entry point: stdout and exit codes
.bunfig.toml                    bun configuration; also the newstack detect marker
tsconfig.json                   editor settings; no packages required
```

No dependencies: only the Bun runtime and its built-in `bun:test` runner, no
`bun install` and no network.

## Requirements

Bun. The runtime is called `bun`, and that is the name in the shebang, so
`./bin/{{ npm_name }}` needs no `chmod` dance.

On macOS or Linux:

```console
$ curl -fsSL https://bun.sh/install | bash
```

## Run

```console
$ ./bin/{{ npm_name }} --help
$ ./bin/{{ npm_name }} README.md
$ cat README.md | ./bin/{{ npm_name }} -w
```

The entry point imports `../src/cli.ts` by relative path, so it works from any
directory, not just the project root.

Output is wc-style, right-aligned: lines, words, bytes, then the path.

```
       3        5       30 sample.txt
```

## Line, word and byte semantics

`lines` is the number of `\n` characters, `words` is the number of maximal
non-whitespace runs, and `bytes` is the length of the UTF-8 encoding of the
text, which is what `wc -c` reports for the file it was read from. A file that
ends without a trailing newline therefore reports one fewer line than it has
visual lines, which is exactly what `wc -l` does. The suite pins this down:

```console
$ printf 'hello' | ./bin/{{ npm_name }}   # 0 lines, 1 word, 5 bytes
$ printf 'hello\n' | ./bin/{{ npm_name }}  # 1 line, 1 word, 6 bytes
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0    | success, including `--help` and `--version` |
| 1    | a file could not be read |
| 2    | usage error: unknown flag, conflicting modes |

## Test

```console
$ bun test
```

`bun test` runs the built-in `bun:test` runner over `tests/*.test.ts` with
nothing to install. `tests/cli.test.ts` spawns `bin/{{ npm_name }}` through
`Bun.spawnSync`, so the exit codes are the ones a shell would see.

## Rename

The file name is the command name. To rename the tool, run `newstack new` into a
new directory with the name you want, or rename `bin/{{ npm_name }}` and update
the references in `README.md`, `.github/workflows/ci.yml`, `package.json`, and
`tests/cli.test.ts`. The TypeScript modules stay `textstat` and `cli`.

## Package identity

newstack renders a lowercase `package_name` with underscores ({{ package_name }})
for languages that need it as an identifier. TypeScript module names here are
fixed (`textstat`, `cli`), so only the dashed `{{ npm_name }}` form is used for
paths: the binary is `bin/{{ npm_name }}` and `--help` prints exactly that name,
so the usage line matches the command.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.

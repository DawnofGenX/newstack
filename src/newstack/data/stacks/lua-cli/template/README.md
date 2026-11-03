# {{ title }}

{{ description }}

A minimal Lua 5.4 command line tool: counting lives in
`src/textstat/counts.lua` (pure functions, no I/O) so tests drive it directly,
parsing lives in `src/textstat/options.lua`, and `bin/{{ npm_name }}` is the thin
entry point that owns argv, stdout/stderr and the exit code.

## Layout

```
bin/{{ npm_name }}             entry point: argv -> help | usage | count, plus os.exit(code)
src/textstat.lua                module facade: require("textstat")
src/textstat/counts.lua         count(): lines, words, bytes — pure, no I/O
src/textstat/options.lua        parse(): argv -> options table — pure, no I/O
spec/harness.lua                hand-rolled describe/it/eq, no dependencies
spec/run.lua                    runner: lua5.4 spec/run.lua
spec/counts_spec.lua            counting edge cases
spec/options_spec.lua           every parser branch
spec/cli_spec.lua               the real script: stdout and exit codes
.luarc.json                     lua-language-server runtime settings
```

No dependencies: only the Lua 5.4 standard library, no luarocks and no network.

## Requirements

Lua 5.4. The interpreter is called `lua5.4` (there is no `lua` symlink on
Debian/Ubuntu), and that is the name in the shebang, so
`./bin/{{ npm_name }}` needs no `chmod` dance.

On Debian or Ubuntu:

```console
$ sudo apt-get install -y lua5.4
```

## Run

```console
$ ./bin/{{ npm_name }} --help
$ ./bin/{{ npm_name }} README.md
$ cat README.md | ./bin/{{ npm_name }} -w
```

The script adds its own `../src` to `package.path`, so it works from any
directory, not just the project root.

Output is wc-style, right-aligned: lines, words, bytes, then the path.

```
       3        5       30 sample.txt
```

## Line, word and byte semantics

`lines` is the number of `\n` bytes, `words` is the number of maximal
non-whitespace runs, and `bytes` is the string length. A file that ends without a
trailing newline therefore reports one fewer line than it has visual lines, which
is exactly what `wc -l` does. The suite pins this down:

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
$ lua5.4 spec/run.lua
```

The runner prints one `ok` line per test, stops at the first failure, and ends
with `N passed, M failed`. Exit status is 0 only when every test passed.
`spec/cli_spec.lua` spawns `bin/{{ npm_name }}` through `io.popen`, so the exit
codes are the ones a shell would see.

## Rename

The file name is the command name. To rename the tool, run `newstack new` into a
new directory with the name you want, or rename `bin/{{ npm_name }}` and update
the shebang-free references in `README.md`, `.github/workflows/ci.yml`, and
`spec/cli_spec.lua`. The Lua module stays `textstat`, which is what
`require("textstat")` resolves through `src/textstat.lua`.

## Package identity

newstack renders a lowercase `package_name` with underscores ({{ package_name }})
for languages that need it as an identifier. Lua module names here are fixed
(`textstat`), so only the dashed `{{ npm_name }}` form is used for paths: the
binary is `bin/{{ npm_name }}` and `--help` prints exactly that name, so the
usage line matches the command.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.

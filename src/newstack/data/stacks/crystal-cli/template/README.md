# {{ title }}

{{ description }}

A minimal Crystal command line tool laid out the way Crystal expects a shard to
be: counting lives in `src/textstat/counts.cr` (pure functions, no I/O),
parsing lives in `src/textstat/options.cr`, `src/textstat/cli.cr` turns a parsed
command line into output and an exit code, and `src/textstat.cr` is the thin
entry point that owns `ARGV`, the standard streams and `exit`.

## Layout

```
shard.yml                    shard manifest: name, `crystal: ">= 1.11.0"`, targets
src/textstat.cr              entry point: requires the modules, exits with CLI.run
src/textstat/counts.cr       Counts.of(text): lines, words, bytes — pure, no I/O
src/textstat/options.cr      Options.parse(argv): mode/files/status — pure, no I/O
src/textstat/cli.cr          CLI.run(args, stdout, stderr) : Int32 — the exit-code contract
spec/spec_helper.cr          requires the modules (never the exit-calling facade)
spec/counts_spec.cr          wc semantics: trailing newline, whitespace, UTF-8 bytes
spec/options_spec.cr         every parser branch: modes, `--`, `-`, help, errors
spec/cli_spec.cr             builds the binary and asserts its real exit codes
```

No dependencies: `shard.yml` has no `dependencies:` block at all, so `crystal
spec` and `crystal build` work offline with no `shards install`.

## Requirements

Crystal 1.11 or newer. The template is developed and tested with Crystal 1.11.2
(LLVM 17); CI installs the latest 1.11.x.

## Build

```console
$ mkdir -p bin
$ crystal build -o bin/{{ npm_name }} src/textstat.cr
```

The binary name comes from the `targets:` entry in `shard.yml`, so a shard-wide
`shards build` produces the same `bin/{{ npm_name }}`. `bin/` is gitignored.

## Run

```console
$ bin/{{ npm_name }} --help
$ bin/{{ npm_name }} README.md
$ cat README.md | bin/{{ npm_name }} -w
```

Output is `wc`-style, right-aligned: lines, words, bytes, then the path.

```
       3        5       30 sample.txt
```

Lines follow `wc -l`: they count `\n` bytes, so a last line without a trailing
newline is not counted. Bytes are raw bytes, so UTF-8 text can be wider than it
looks.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0    | success, including `--help` and `--version` |
| 1    | a file could not be read (other files are still counted) |
| 2    | usage error: unknown flag, conflicting modes |

`Textstat::CLI.run` *returns* these codes; only `src/textstat.cr` calls `exit`,
which is what lets `spec/cli_spec.cr` assert them by running the compiled binary.

## Test

```console
$ crystal spec
```

`crystal spec` compiles `spec/**/*_spec.cr` and runs them. `spec/cli_spec.cr`
builds `src/textstat.cr` into a temporary directory with `crystal build`, then
runs it as a child process so exit codes 0/1/2 and stdout/stderr are proven at
the process boundary. Nothing needs the network.

## Package identity and renaming

The binary is `{{ npm_name }}` (from the shard's `targets:` entry) and `--help`
prints exactly that name. The Crystal *module* and the source directory are
deliberately fixed as `Textstat` / `src/textstat`, because Crystal resolves
`require "./textstat/counts"` by path and the module name is what the specs and
the CLI refer to.

To rename the module (say to `Wordcount`):

1. `git mv src/textstat.cr src/wordcount.cr` and `git mv src/textstat src/wordcount`
2. In every `src/**/*.cr` and `spec/**/*.cr`, replace `Textstat` with `Wordcount`
   and `require "./textstat/` with `require "./wordcount/` (plus the
   `spec_helper.cr` require of `../src/textstat/cli`).
3. Update `targets:` in `shard.yml`: `main: src/wordcount.cr`, and keep the
   binary key you want.
4. Update `PROGRAM` in `src/wordcount/cli.cr` to the binary name, so the usage
   line still matches the command.

Renaming just the *binary* is easier: change the `targets:` key in `shard.yml`
and `PROGRAM` in `src/textstat/cli.cr` together.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) {{ year }} {{ author }}.

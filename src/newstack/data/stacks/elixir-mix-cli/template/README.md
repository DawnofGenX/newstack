# {{ title }}

{{ description }}

A small Elixir command line tool: counting lives in a pure module
(`Textstat.Counter`, `Textstat.Counts`) so ExUnit drives it directly, and
`Textstat.CLI` is a thin shell around argv, output and the exit code.
`escript` turns it into a single runnable binary, no runtime dependencies.

## Layout

```
mix.exs                              app atom from the project name, escript config
lib/textstat/counts.ex               line / word / byte struct
lib/textstat/counter.ex              pure counting, no I/O
lib/textstat/options.ex              hand-rolled argv parsing and help text
lib/textstat/cli.ex                  reads files or stdin, prints, returns an exit code
test/textstat/counter_test.exs       ExUnit tests for counting
test/textstat/options_test.exs       ExUnit tests for parsing
test/textstat/cli_test.exs           ExUnit tests for output and exit codes
```

`System.halt/1` is called in `Textstat.CLI.main/1` only, so tests exercise
`run/2` and assert on return values instead of trapping exits.

## Build

```console
$ mix deps.get
$ MIX_ENV=prod mix escript.build
```

The binary is `{{ npm_name }}` in the project root.

## Run

```console
$ ./{{ npm_name }} --help
$ ./{{ npm_name }} README.md
$ printf 'one two\nthree\n' | ./{{ npm_name }} -w
```

`-l`, `-w` and `-c` select lines, words or bytes; with no flag all three are
printed. Bad usage exits `2`, an unreadable file exits `1`.

## Test

```console
$ mix test
$ mix format --check-formatted
```

## License

MIT — see [LICENSE](LICENSE).

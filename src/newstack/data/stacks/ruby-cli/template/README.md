# {{ title }}

{{ description }}

A Ruby command line tool in the shape a gem takes: the counting logic lives in a
library (`lib/textstat/`), the binary (`bin/{{ npm_name }}`) only wires stdin,
stdout and an exit code to it, and the tests drive the library directly.

## Layout

```
lib/textstat/counts.rb    Textstat.count(text) -> Counts(lines:, words:, bytes:)
lib/textstat/options.rb   Options.parse(argv)  -> flags, paths, or UsageError
lib/textstat/cli.rb       CLI#run(argv)        -> exit code, I/O injected
bin/{{ npm_name }}             the executable
test/                     minitest: counts, options, and the CLI through StringIO
```

Everything is on the standard library — minitest and rake ship with Ruby, so
there is nothing to install before the tests run.

## Run

```console
$ echo "a b" | bin/{{ npm_name }}
      1      2      4

$ bin/{{ npm_name }} -c README.md
   1234

$ bin/{{ npm_name }} --json README.md
{"lines":42,"words":300,"bytes":1900,"path":"README.md"}
```

No file argument (or `-`) reads stdin. `-l`, `-w` and `-c` select lines, words
and bytes; with no flag all three are printed wc-style. `--help` and `--version`
exit 0, a missing file exits 1 and does not stop the remaining arguments, and an
unknown option exits 2 with the usage line on stderr.

The counting rules are the wc ones: lines are `\n` bytes, words are runs of
anything outside `[ \t\n\r\v\f]`, and bytes are the UTF-8 length, so
`"héllo wörld\n"` is one line, two words and fourteen bytes.

## Test

```console
$ rake test
```

`test/cli_test.rb` runs the real `CLI` with `StringIO` for stdin/stdout/stderr
and a stub reader for files, so the suite never spawns a process.

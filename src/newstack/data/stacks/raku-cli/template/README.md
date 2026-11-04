# {{ title }}

A command line tool that counts newlines, words, and bytes, written in
[Raku](https://raku.org/) on Rakudo. It is the `wc` classic, narrowed to `-l`,
`-w`, and `-c`, with a test suite that needs no framework.

## Run it

```console
$ {{ npm_name }} sample.txt
 2  4 23 sample.txt
$ printf 'alpha beta\ngamma\n' > sample.txt
$ {{ npm_name }} -w sample.txt
3 sample.txt
$ printf 'alpha beta\ngamma\n' | {{ npm_name }} -w
3
$ printf 'alpha beta\ngamma\n' | {{ npm_name }} -w -
3 -
```

The column width follows `wc`: one figure from one readable operand is not
padded, a pipe gets the seven-wide cells, and everything else is as wide as the
byte total. A `total` row appears as soon as there is more than one operand,
even when one of them could not be read.

## Layout

```
main.raku                      the only file that touches a handle or an exit code
lib/Textstat/Counts.rakumod    Buf in, Counts object out
lib/Textstat/Options.rakumod   argv in, Parsed object out
lib/Textstat/Runner.rakumod    the decision, with reading and writing handed in
tests/Harness.rakumod          a tally and two buffers
tests/run-tests.raku           three suites feeding the runner fake handles
```

Each module states what it exports; the counting core never sees a handle and
the parser never sees the terminal. `{{ npm_name }}` runs
`raku -I lib main.raku`, so there is no build step.

## Test

```console
$ raku -I lib -I tests tests/run-tests.raku
checks: 82, passed: 82, failed: 0
```

The suites hand the runner closures, so a formatting slip fails without
spawning a process; the shipped `stdin` check is what covers the real pipe
path.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | everything asked for was counted |
| 1 | a file could not be read (the rest were still counted) |
| 2 | the arguments were wrong |

## Licence

MIT. See `LICENSE`.

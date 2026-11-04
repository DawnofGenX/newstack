# {{ npm_name }}

A word-count CLI in Groovy. It prints the newline, word and byte counts of the
files you name, exactly like `wc -l -w -c`, and it ships with a test suite that
needs nothing but the Groovy runtime.

```
$ ./bin/{{ npm_name }} --help
Usage: {{ npm_name }} [OPTION]... [FILE]...

Print newline, word, and byte counts for each FILE.

  -l, --lines    print the newline counts
  -w, --words    print the word counts
  -c, --bytes    print the byte counts
  -h, --help     show this help and exit
  -V, --version  show the version and exit

With no FILE, or when FILE is -, read standard input.
```

## Try it

```
$ printf 'alpha beta\ngamma delta\n' > sample.txt
$ ./bin/{{ npm_name }} sample.txt
 2  4 23 sample.txt
$ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
3
$ ./bin/{{ npm_name }} missing.txt
error: cannot open 'missing.txt'
$ echo $?
1
```

The figures are within a few bytes of `wc`, because they are the same figures:
lines are newline bytes, words are runs of non-whitespace bytes, and the byte
count is the length of the file. Nothing is decoded as text, so a multi-byte
character counts as several bytes.

## Layout

```
main.groovy              the only file that touches the process
src/textstat/
  Counts.groovy          counting over a byte array
  Options.groovy         the argv parser
  Runner.groovy          rows, widths, exit codes
tests/
  Harness.groovy         assertions and one report line
  run_tests.groovy       every case, no framework
bin/{{ npm_name }}       a shell wrapper that finds its own root
```

`Runner` takes its four side effects as closures — reading a file, reading
standard input, writing to stdout, writing to stderr — so every case in the
suite drives the real logic without spawning a process. `main.groovy` is the
only place that opens a file or calls `System.exit`.

## Run the tests

```
$ groovy -cp src:tests tests/run_tests.groovy
checks: 83, passed: 83, failed: 0
```

There is no build step and no dependency to install: `groovy` on the path is
the whole toolchain. The suite exits non-zero the moment a case fails, so CI
can run that single command.

## Exit codes

- `0` — everything named was counted (and for `--help` and `--version`)
- `1` — at least one file could not be read; the others are still counted
- `2` — the arguments were wrong; nothing is counted

## Licence

MIT. See [LICENSE](LICENSE).

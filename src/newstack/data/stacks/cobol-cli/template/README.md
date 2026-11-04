# {{ npm_name }}

A small `wc`-shaped counter written in COBOL, built with GNUCOBOL. It reports
newlines, words and bytes for each operand and reads standard input when there
is nothing else to read.

The point of the project is the shape, not the counter: the counting lives in a
subprogram, the argument parser is another subprogram, and only one program
touches the outside world. That is why the unit driver can check the first two
without ever starting a process.

## Requirements

`cobc` (GNUCOBOL 3.x) and `make`.

```console
$ sudo apt-get install -y --no-install-recommends gnucobol make
```

## Quick start

```console
$ make all
$ ./bin/{{ npm_name }} --help
Usage: {{ npm_name }} [OPTION]... [FILE]...
Print newline, word, and byte counts for each FILE.

  -l, --lines    print the newline count
  -w, --words    print the word count
  -c, --bytes    print the byte count
  -h, --help     show this help and exit
  -V, --version  show the version and exit

With no FILE, or when FILE is -, read standard input.
```

```console
$ printf 'alpha beta\ngamma delta\n' > sample.txt
$ ./bin/{{ npm_name }} sample.txt
 2  4 23 sample.txt
$ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
3
$ ./bin/{{ npm_name }} -l sample.txt
2 sample.txt
$ ./bin/{{ npm_name }} -l sample.txt sample.txt
 2 sample.txt
 2 sample.txt
 4 total
$ ./bin/{{ npm_name }} --bogus
{{ npm_name }}: unknown option: --bogus
Try '{{ npm_name }} --help' for more information.
```

The exit code is 0 when every operand was counted, 1 when one could not be
read, and 2 for a usage error. A read failure still contributes to the `total`
row, which is what `wc` does.

## Layout

```
src/main.cob                 the process: reads /proc/self/cmdline, sets the exit code
src/textstat-options.cob     turns argv into a decision, no I/O
src/textstat-counts.cob      the counter itself, fed byte blocks
src/textstat-runner.cob      the only program that opens files and prints
tests/textstat-tests.cob     unit driver: PASS/FAIL per assertion
tests/run_tests.sh           the driver plus checks against the real wc
bin/{{ npm_name }}           builds once, then execs the binary
```

## How it counts

`TEXTSTAT-COUNTS` keeps three `PIC 9(18) COMP-5` counters and consumes a block
of bytes per call, so the caller decides how the bytes arrive. A newline is
`X"0A"`; a word starts at a byte that is not one of space, tab, newline,
carriage return, vertical tab (`X"0B"`) or form feed (`X"0C"`).

Files are read through a one-byte record layout:

```cobol
       SELECT F-DATA ASSIGN TO WS-PATH
           ORGANIZATION IS SEQUENTIAL
           FILE STATUS IS WS-FS.
```

One-byte records return every byte of the file, including newlines and NULs,
which `ACCEPT` or a line-oriented read would swallow. Standard input is opened
the same way through `/dev/stdin`, so a pipe and a redirect behave alike.

## How argv is parsed

`ACCEPT ... FROM ARGUMENT-NUMBER` is not available in every GNUCOBOL build, so
`main.cob` reads `/proc/self/cmdline` with the same one-byte reader and splits
it on `LOW-VALUE`. The first word is the program's own path and is skipped; the
rest are handed to `TEXTSTAT-OPTIONS`, which understands `--`, long options,
short clusters such as `-lwc`, and a lone `-` as a file name. With no figure
option every figure is printed, exactly like `wc`.

## Tests

```console
$ make test
...
checks: 71, passed: 71, failed: 0
```

`tests/textstat-tests.cob` calls the counting and parsing subprograms directly
and prints one line per assertion. `tests/run_tests.sh` runs that driver, then
compares the built tool with the machine's own `wc` on a set of fixtures —
including a file without a trailing newline, a UTF-8 file, an empty file, a
control-character file and a 1201-byte file that forces the wide column
padding.

## Where this deliberately differs from wc

`wc` prints a `0 0 0` row and `Is a directory` for a directory operand. This
tool refuses it with `error: cannot open` and exit 1 instead, because a
directory is not a text file and silently reporting zeroes hides a mistake.

## Licence

MIT, see `LICENSE`.

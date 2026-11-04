# {{ title }}

{{ description }}

A tiny `wc`-shaped command-line tool, written so the parts are visible: a
byte-exact counting unit, a hand-written argv parser, and a program that talks
to the terminal. Nothing outside the Free Pascal RTL is used, and the suite is
hand-rolled — no fpcunit, no Lazarus.

```console
$ make
$ make test
checks: 47, passed: 47, failed: 0
$ ./bin/{{ npm_name }} --help
Usage: {{ npm_name }} [OPTION]... [FILE]...
Count lines, words and bytes. With no FILE, or when FILE is -, read standard input.
  -l, --lines     print the newline count
  -w, --words     print the word count
  -c, --bytes     print the byte count
```

## Using it

```console
$ printf 'alpha beta\ngamma delta\n' > sample.txt
$ ./bin/{{ npm_name }} sample.txt
 2  4 23 sample.txt
$ printf 'one two\n' > second.txt
$ ./bin/{{ npm_name }} sample.txt second.txt
 2  4 23 sample.txt
 1  2  8 second.txt
 3  6 31 total
$ printf 'one line, no trailing newline' | ./bin/{{ npm_name }} -c
29 -
```

Figures are right-aligned to one shared width, columns are separated by single
spaces, and the label comes last, so the output lines up the way `wc` does. A
`total` row appears whenever there is more than one operand — including when
one of them could not be read.

`{{ npm_name }}` exits `0` on success, `1` when a file could not be read, and `2`
for a usage error.

## Layout

```
src/textstat_counts.pas    byte counting, the part that has to agree with wc
src/textstat_options.pas   argv -> TOptions; never touches the process
src/textstat_runner.pas    the program: formatting, exit codes, total row
src/main.pas               the only unit that opens a file, writes to a
                           terminal or sets the exit code
tests/run_tests.pas        47 assertions, no third-party test framework
bin/{{ npm_name }}               builds on first use, then execs the binary
```

The seam between `textstat_runner` and the world is a record of function
pointers:

```pascal
TIo = record
  ReadFile: TReader;   { function(const path: string; out ok: Boolean): TRawBytes }
  WriteOut: TWriter;
  WriteErr: TWriter;
end;
```

so the suite drives the whole contract — rows, error text and exit codes —
without spawning a process or writing a temporary file.

## Building on Windows and macOS

The sources are plain Free Pascal; only `src/main.pas` is Unix-specific, because
it reads file descriptors with `BaseUnix`. The units, the parser and the test
suite are portable, which is what makes the exit-code contract testable
anywhere.

## Notes

- `make` writes objects to `obj/` and binaries to `build/`; both are ignored.
- `fpc` prints its version banner even in quiet mode. The wrapper sends build
  output to stderr, so stdout stays clean on the first run.
- Line counting follows `wc`: newlines are counted, so a file that does not end
  in a newline reports one fewer line than it has text lines.

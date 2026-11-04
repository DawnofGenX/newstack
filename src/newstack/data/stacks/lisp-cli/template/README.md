# {{ project_name }}

A `wc`-style counter written in Common Lisp on SBCL, with no dependency outside the
standard library.

```console
$ ./bin/{{ npm_name }} sample.txt
 2  4 23 sample.txt
$ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
3 -
$ ./bin/{{ npm_name }} sample.txt second.txt
 2  4 23 sample.txt
 1  1  2 second.txt
 3  5 25 total
```

## Layout

```
main.lisp              the only file that touches the process: files, stdin, exit
lib/counts.lisp        byte-exact counting, plus adding two tallies
lib/options.lisp       argv parsing: figures, files, --, unknown options
lib/runner.lisp        the program, with reads and writes injected
tests/harness.lisp     the four helpers the suites share
tests/*-tests.lisp     counts, options, runner
tests/run-tests.lisp   loads everything, prints a tally, exits non-zero on failure
bin/{{ npm_name }}       wrapper: sbcl --script, so the sources need no build step
```

## How it counts

Bytes are read as `(unsigned-byte 8)` and folded once: a byte of 10 ends a line, any of
space/tab/newline/vertical tab/form feed/carriage return separates words, and every other
byte continues the current word. The byte count is the length of the data, so a multibyte
character counts as the bytes it occupies — the numbers match `wc -l -w -c` exactly.

`lib/runner.lisp` never calls `read`, `write` or `exit`. It takes an `io` structure of four
functions, which is why the test suite can drive the whole program — exit codes, total
row and error text included — without spawning a process.

## Running it

```console
$ sbcl --script tests/run-tests.lisp
checks: 69, passed: 69, failed: 0
```

With a file argument the program prints one right-aligned row per operand and a `total`
row when there is more than one. With no operand, or with `-`, it reads standard input.

An unreadable operand prints `{{ npm_name }}: cannot open '<path>'` on stderr, contributes no
row, and exits 1. A bad option exits 2 after printing `Try '{{ npm_name }} --help'`.

# {{ npm_name }}

A count-lines-words-bytes tool, in Tcl.  It is the newstack `tcl-cli` starter:
small enough to read in one sitting, shaped like a real project.

## What is here

    bin/{{ npm_name }}          the command people run
    main.tcl              reads the real filesystem, stdin and stdin channels
    lib/counts.tcl        byte-level counting, the part worth testing
    lib/options.tcl       a hand-written argv parser
    lib/runner.tcl        decides what to print and which code to exit
    tests/                a 40-check suite with no dependencies

`counts`, `options` and `runner` know nothing about a process: the runner takes
a dictionary of `readFile`, `readStdin`, `out` and `err`, so the tests can hand
it a fake filesystem and two real temporary channels.  Only `main.tcl` opens a
file, touches stdin and calls `exit`.

## Getting started

    tclsh tests/run.tcl
    ./bin/{{ npm_name }} --help

No dependencies, no package manager, no build step: `tclsh` (8.6 or newer) is
all it needs.  The tests are plain Tcl, not tcltest — `harness.tcl` is a
twenty-line counter, so a failing check names itself and the suite exits with
the number of failures.

## Using it

    $ printf 'alpha beta\ngamma\n' > sample.txt
    $ ./bin/{{ npm_name }} sample.txt
     2  3 17 sample.txt
    $ ./bin/{{ npm_name }} -w sample.txt
    3 sample.txt
    $ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
    3 -

The numbers are `wc -l -w -c`'s, byte for byte: lines are newline bytes, words
are maximal runs of non-whitespace, and bytes are bytes (a UTF-8 character can
be several).  Columns are right-aligned to a single width and separated by one
space, with the label last, which is what `wc` does.

Exit codes: `0` success, `1` a file could not be read (the others are still
counted), `2` a usage error.

## Where the projections are

* the counting rule lives in `counts.tcl`, and the tests in
  `tests/counts_test.tcl` are the specification;
* the parser never touches the filesystem, so `tests/options_test.tcl` is a
  table of argv in, dictionary out;
* the runner's exit codes are tested against a fake boundary, and the shipped
  workflow additionally pipes real text through the real binary, because a fake
  boundary cannot see a broken stdin path.

## Licence

MIT, see `LICENSE`.

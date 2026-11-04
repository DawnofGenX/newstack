# {{ npm_name }}

A count-lines-words-bytes tool, in Racket.  It is the newstack `racket-cli`
starter: no packages beyond the core distribution, no build step, tests you can
run with one command.

## What is here

    bin/{{ npm_name }}          the command people run
    textstat/counts.rkt      byte-level counting, the part worth testing
    textstat/options.rkt     a hand-written argv parser (structs, no side effects)
    textstat/runner.rkt      decides what to print and which code to exit
    main.rkt                 files, stdin, stdout, exit
    tests/                   rackunit suites, 54 checks

`counts`, `options` and `runner` are pure: the runner takes a `struct io` of four
funs (`read-file`, `read-stdin`, `out`, `err`), so its tests hand it a hash of
in-memory files and collect the output in a string port.  Only `main.rkt` opens
a file, reads the real stdin and calls `exit`.

## Getting started

    raco test tests/    # the whole suite
    ./bin/{{ npm_name }} --help

There is nothing to install: `racket` and `raco` ship together.

## Using it

    $ printf 'alpha beta\ngamma\n' > sample.txt
    $ ./bin/{{ npm_name }} sample.txt
     2  3 17 sample.txt
    $ ./bin/{{ npm_name }} -w sample.txt
    3 sample.txt
    $ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
    3 -

The numbers are `wc -l -w -c`'s, byte for byte: counting works on `bytes?` with
`bytes-ref` and `bytes-length`, because "a character" is an encoding question
and `wc` answers it in bytes.  Columns are right-aligned to a single width and
separated by one space, with the label last.

Exit codes: `0` success, `1` a file could not be read (the rest are still
counted), `2` a usage error.

## Why the io struct

The runner is where the interesting decisions are: stdout or stderr, `0`, `1`
or `2`, and how wide the columns are.  Four funs make all of that testable
without starting a process, and they keep `exit` in one place.  The shipped
workflow still pipes real text through the real command, because a fake
boundary cannot see a broken stdin path.

## Licence

MIT, see `LICENSE`.

# {{ npm_name }}

A count-lines-words-bytes tool, in Erlang.  It is the newstack `erlang-cli`
starter: small enough to read in one sitting, shaped like a real project.

## What is here

    bin/{{ npm_name }}            the command people run
    lib/textstat_counts.erl     byte-level counting, the part worth testing
    lib/textstat_options.erl    a hand-written argv parser
    lib/textstat_runner.erl     decides what to print and which code to exit
    lib/textstat_main.erl       files, stdin, stdout, exit
    test/                       three eunit modules, 42 tests
    Makefile                    erlc for the libs, `make test` for eunit

`counts`, `options` and `runner` take no process arguments: the runner's whole
IO surface is a map of four funs (`read_file`, `read_stdin`, `out`, `err`), so
the tests hand it a fake filesystem and collect its output as messages.  Only
`textstat_main` reads a file, opens stdin and calls `halt/1`.

## Getting started

    make            # compile lib/ into ebin/
    make test       # eunit: the whole suite
    ./bin/{{ npm_name }} --help

The wrapper builds on first use if `ebin/` is missing, so `./bin/{{ npm_name }}` works
in a fresh checkout.  No rebar, no hex packages: OTP and `make` are the whole
toolchain.

## Using it

    $ printf 'alpha beta\ngamma\n' > sample.txt
    $ ./bin/{{ npm_name }} sample.txt
     2  3 17 sample.txt
    $ ./bin/{{ npm_name }} -w sample.txt
    3 sample.txt
    $ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
    3 -

The numbers are `wc -l -w -c`'s, byte for byte: counting works on binaries
(`binary_to_list/1`, `byte_size/1`), because "a character" is a locale question
and `wc` answers it in bytes.  Columns are right-aligned to a single width and
separated by one space, with the label last — the same layout `wc` produces.

Exit codes: `0` success, `1` a file could not be read (the others are still
counted), `2` a usage error.

## Why the IO map

The runner is the interesting boundary: it decides between stdout and stderr,
between `0`, `1` and `2`, and how to align a table.  Handing it four funs means
those decisions are testable without starting a process, and it keeps `halt/1`
in exactly one module.  The shipped workflow still pipes real text through the
real binary, because a fake boundary cannot see a broken stdin path.

## Licence

MIT, see `LICENSE`.

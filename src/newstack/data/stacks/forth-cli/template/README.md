# Project title

A Forth CLI on `gforth`: it counts newlines, words and bytes the way `wc` does,
with the counting core, the argv parser and the terminal kept apart.

## Layout

    main.fs            the entry point: argv in, exit status out
    lib/counts.fs      byte-exact counting over a memory block
    lib/options.fs     the argv parser: flags, clusters, -- and input files
    lib/runner.fs      reads the operands, pads the columns, prints the rows
    tests/run_tests.fs 64 unit checks in Forth
    tests/run_tests.sh the same checks plus comparisons against the host wc
    bin/NAME           runs main.fs with gforth and passes the exit status on

Only `main.fs` and `lib/runner.fs` touch the process: they open the files, read
standard input and write the rows. The rest is pure words over a block.

## Running it

    ./bin/NAME sample.txt
    ./bin/NAME -l -w sample.txt
    printf 'alpha beta\ngamma\n' | ./bin/NAME -c

    sh tests/run_tests.sh

## What it prints

    $ printf 'alpha beta\ngamma delta\n' > sample.txt
    $ ./bin/NAME sample.txt
     2  4 23 sample.txt
    $ printf 'alpha beta\ngamma\n' | ./bin/NAME -w
    3

With no FILE, or when FILE is `-`, it reads standard input. The column width
and the `total` row follow `wc`: one figure over a single operand keeps its own
width, a pipe pads to seven columns, and the width is otherwise the digit count
of the total bytes read.

Exit status is 0 on success, 1 when a file cannot be read, 2 on a usage error.

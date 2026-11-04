# {{ npm_name }}

A count-lines-words-bytes tool, in TypeScript on Deno.  It is the newstack
`deno-cli` starter: no `package.json`, no `node_modules`, one runtime that is
also the test runner and the typechecker.

## What is here

    bin/{{ npm_name }}       the command people run
    main.ts             the entry point: real IO in, exit code out
    src/counts.ts       byte-level counting, the part worth testing
    src/options.ts      a hand-written argv parser, a pure function
    src/runner.ts       decides what to print and which code to exit
    src/io.ts           the only module that touches the process
    tests/              Deno.test suites, 24 tests

`src/counts.ts`, `src/options.ts` and `src/runner.ts` are pure: the runner takes
an object of four functions (`readFile`, `readStdin`, `out`, `err`), so its
tests hand it in-memory files and collect the output in a string.  Only
`src/io.ts` reads a real file, touches stdin and writes to the terminal.

## Getting started

    deno task test      # or: deno test
    deno check main.ts  # typecheck, no build output
    ./bin/{{ npm_name }} --help

Deno runs TypeScript directly, so there is no build step and no transpiled
copy of the tree to keep in sync.  The wrapper passes `--allow-read`; nothing
else is granted, which is why the counting core takes bytes instead of paths.

## Using it

    $ printf 'alpha beta\ngamma\n' > sample.txt
    $ ./bin/{{ npm_name }} sample.txt
     2  3 17 sample.txt
    $ ./bin/{{ npm_name }} -w sample.txt
    3 sample.txt
    $ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
    3 -

The numbers are `wc -l -w -c`'s, byte for byte: counting works on `Uint8Array`
with a byte-level view of whitespace, because "a character" is an encoding
question and `wc` answers it in bytes.  Columns are right-aligned to a single
width and separated by one space, with the label last.

Exit codes: `0` success, `1` a file could not be read (the rest are still
counted), `2` a usage error.

## Why the IO object

The permission model makes the boundary explicit: the runner cannot read a file
even if it wanted to, because all it has is a function.  That is also what makes
the tests fast — no temp directories, no child processes — and it keeps
`Deno.exit` in one place.  The shipped workflow still pipes real text through
the real command, because a fake boundary cannot see a broken stdin path.

## Licence

MIT, see `LICENSE`.

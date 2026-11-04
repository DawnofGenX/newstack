# {{ title }}

{{ description }}

A byte-exact `wc` replacement written in Octave with no dependencies beyond
`octave` itself. The counting core, the argument parser and the runner are
plain functions in the `+textstat` package; only `main.m` touches the real
process, and it hands the runner a struct of function handles so the suite can
inject its own stdin, files and output buffers.

## Layout

`main.m`                 entry point: real stdin, files and output
`+textstat/counts.m`     line, word and byte counts for a byte vector
`+textstat/parse_options.m`  argv to `{status, figures, files, message}`
`+textstat/run.m`        the whole CLI against an injected environment
`tests/run_tests.m`      58 checks, no framework, exits non-zero on a failure

## Use

    ./bin/{{ npm_name }} sample.txt
    ./bin/{{ npm_name }} -l -w src/*.m
    printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w

Sample, with `sample.txt` holding `alpha beta\ngamma delta\n`:

    $ ./bin/{{ npm_name }} sample.txt
     2  4 23 sample.txt
    $ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
    3 -

The figures are right-aligned to one width shared by every printed row, a
`total` row appears when more than one file is named, and `-` (or no operand
at all) reads standard input.

## Test

    octave --no-window-system --quiet tests/run_tests.m
    checks: 58, passed: 58, failed: 0

## Notes

Octave single-quoted strings do not interpret escapes: `'a\nb'` is four
characters. Fixtures in the suite are built with `sprintf` for that reason.

`main.m` starts with `1;` so Octave treats it as a script rather than a
function file, which is what lets it define helper functions and then run the
top-level code at the end.

# {{ title }}

A dependency-free SWI-Prolog Sudoku solver. It picks the most constrained
empty cell at each step, respects row, column and 3x3 box rules, and reports
every solution it finds up to a configurable limit. The solver, option parser
and CLI are separate modules; the CLI reads through an injected predicate.

## Usage

```sh
./bin/{{ npm_name }} grid.txt
./bin/{{ npm_name }} --limit 2 grid.txt
swipl -q -f tests/run_tests.pl
```

`grid.txt` has nine lines of nine characters; `.` marks an empty cell. The
output starts with a `solutions: N` line, then each solution as nine rows.
Exit status is 0 on success, 1 on a read or grid error, 2 on a usage error.

## Layout

- `lib/sudoku.pl` — grid parsing, candidate computation and backtracking
- `lib/options.pl` — hand-written option parser
- `lib/runner.pl` — CLI with injected output and file readers
- `tests/run_tests.pl` — dependency-free assertions

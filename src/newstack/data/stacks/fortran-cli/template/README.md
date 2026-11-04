# {{ title }}

{{ description }}

A word-count style command line tool in modern Fortran (2018), built with
`gfortran` and `make`. No dependencies beyond the compiler.

## Layout

```
src/textstat_counts.f90    counting core: a counter_t you feed bytes to
src/textstat_options.f90   argv parsing, no I/O
src/textstat_runner.f90    the program logic, takes output units as arguments
src/main.f90               the only place that touches real argv and units
tests/run_tests.f90        a hand-written harness, no test framework
bin/{{ npm_name }}         wrapper: builds on first use, then execs the binary
Makefile                   APP ?= {{ npm_name }}
```

The counting is split from the printing, and the runner takes its output units
as arguments, so the test suite reads what the tool would have written without
starting a process.

## Build and test

```
make            # builds build/{{ npm_name }}
make test       # compiles and runs the suite
./bin/{{ npm_name }} --help
```

`make test` builds into `build/` and leaves it there; `make clean` removes the
directory.

## Usage

```
$ printf 'alpha beta\ngamma delta\n' > sample.txt
$ {{ npm_name }} sample.txt
 2  4 23 sample.txt
$ printf 'alpha beta\ngamma\n' | {{ npm_name }} -w
3 -
$ {{ npm_name }} -l src/main.f90 tests/run_tests.f90
 19 src/main.f90
277 tests/run_tests.f90
296 total
```

Flags are `-l` (lines), `-w` (words), `-c` (bytes); the long forms are
`--lines`, `--words` and `--bytes`. With no flag all three figures print. With
no file, or with `-`, the tool reads standard input. Exit codes: `0` when every
file was counted, `1` when a file could not be read, `2` for a usage error.

## Notes

Standard input is read a byte at a time through a stream connection to
`/dev/stdin`. That is the only way to be exact: Fortran's formatted input
invents a newline it never saw, and `inquire(size=)` cannot measure a pipe.

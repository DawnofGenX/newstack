# {{ title }}

{{ description }}

A dependency-free C11 command line tool. Counting lives in a `textstat` library
(`include/textstat/`, `src/`) so it can be tested directly, and `src/main.c` is a
thin binary that turns argv into output and an exit code. GNU make builds both;
the test suite is a 40-line assertion header, not a framework.

## Layout

```
Makefile                      builds build/{{ npm_name }} and build/tests, C11, warnings are errors
include/textstat/counters.h   struct textstat_counts and textstat_count()
include/textstat/options.h    flag parsing, help text, version
src/counters.c                line / word / byte counting
src/options.c                 hand-rolled argv parsing, no getopt
src/main.c                    reads files or stdin, prints counts, sets the exit code
tests/check.h                 CHECK / CHECK_SIZE / CHECK_TEXT macros
tests/test_counters.c         counting cases, including blank lines and UTF-8
tests/test_options.c          flag parsing, `--`, unknown options, stdin default
tests/main.c                  runs every suite and exits non-zero on failure
```

No third-party dependencies and nothing is downloaded: `make` and `make test` work
offline with any C11 compiler.

## Build

```console
$ make
$ make test
```

`-Wall -Wextra -Wpedantic -Werror` is on, so a warning in this project is a build
failure — fix it or turn the specific warning off with a comment explaining why.

## Run

```console
$ ./build/{{ npm_name }} --help
$ ./build/{{ npm_name }} README.md
$ printf 'one two\nthree\n' | ./build/{{ npm_name }} -w
```

`-l`, `-w` and `-c` select lines, words or bytes; with no flag all three are
printed. No file (or `-`) reads stdin. Several files print a `total` row. Bad usage
exits `2`, an unreadable file exits `1`.

## Where to grow

- Add a source file to `LIB_SRCS` in the `Makefile`; the pattern rules pick it up.
- Add a suite as `tests/test_<name>.c` exporting `int run_<name>_tests(void)` and
  call it from `tests/main.c`.
- Run `make clean` before reporting a build bug: stale objects hide header changes.

## License

MIT — see [LICENSE](LICENSE).

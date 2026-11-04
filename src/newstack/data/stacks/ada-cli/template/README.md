# {{ title }}

A small command-line counter in Ada, built by [newstack](https://github.com/DawnofGenX/newstack).
It prints the number of lines, words and bytes in each file, the way `wc -l -w -c`
does, and it is byte-for-byte identical to `wc` on the same input.

{{ description }}

## Requirements

- GNAT (the Ada compiler; `gnatmake` drives it) — `apt-get install gnat`
- `make`

## Build

```console
$ make
```

The binary lands in `build/{{ npm_name }}`. `./bin/{{ npm_name }}` builds it on
first use and then execs it, so you can skip this step.

## Test

```console
$ make test
checks:  71, passed:  71, failed:  0
```

The suite is dependency-free: `tests/harness.adb` is a forty-line checker, and
`tests/run_tests.adb` calls the counting core, the option parser and the runner
directly. The runner takes its two output subprograms as parameters, so the
suite captures text instead of spawning a process; only `src/main.adb` touches
the real standard input, output and exit status.

## Use

```console
$ printf 'alpha beta\ngamma delta\n' > sample.txt
$ ./bin/{{ npm_name }} sample.txt
 2  4 23 sample.txt
$ printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }} -w
3 -
$ ./bin/{{ npm_name }} --help
Usage: {{ npm_name }} [-l] [-w] [-c] [FILE...]
Count lines, words and bytes. With no FILE, or with -, read stdin.
```

Exit status: `0` when every operand was counted, `1` when a file could not be
read (the other operands are still counted and a `total` row is still printed),
`2` for a usage error.

## Layout

```
src/textstat.ads            parent package, so the child units can be named
src/textstat-counts.ads     the figure set, the tally and the counting core
src/textstat-counts.adb
src/textstat-options.ads    argv parsing: no I/O, returns a Parsed record
src/textstat-options.adb
src/textstat-runner.ads     program logic; output goes through two Writer parameters
src/textstat-runner.adb
src/textstat-output.ads     the only unit that writes to the real stdout/stderr
src/textstat-output.adb
src/main.adb                wires Ada.Command_Line to the runner
tests/harness.ads           pass/fail counters and two capture buffers
tests/harness.adb
tests/run_tests.adb         the 71 checks
bin/{{ npm_name }}          build-on-first-use wrapper
```

GNAT maps `Textstat.Options` to `textstat-options.ads` — the hyphen is the
compiler's rule, not a typo. The counting core works on bytes, so a file whose
last line has no newline still has its words counted, exactly like `wc`.

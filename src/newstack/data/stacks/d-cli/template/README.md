# {{ project_name }}

{{ description }}

A command line tool written in [D](https://dlang.org/) and compiled with LDC into a
single native binary. It counts newlines, words and bytes exactly the way `wc` does —
same figures, same column widths, same exit codes — and proves it by diffing its
output against the real `wc`.

## Requirements

- LDC 1.36 or newer (`apt-get install ldc` on Debian and Ubuntu), which also provides
  the D standard library
- `make` (optional, but the workflows use it)

## Quick start

```sh
make build
./bin/{{ npm_name }} --help
./bin/{{ npm_name }} README.md
printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }}
```

`./bin/{{ npm_name }}` compiles on first run, so `make build` is a convenience
rather than a requirement.

## What it does

```
$ wc README.md
 44  281 1802 README.md
$ ./bin/{{ npm_name }} README.md
 44  281 1802 README.md
```

`-l`, `-w` and `-c` (and `--lines`, `--words`, `--bytes`) select the figures; they
can be clustered (`-lw`). With no file, or with `-`, it reads standard input. Two or
more operands add a `total` row, and an unreadable operand is reported on stderr
while the rest are still counted.

## Exit codes

| Code | Meaning |
| ---- | ------- |
| 0 | every operand was counted |
| 1 | at least one operand could not be read |
| 2 | usage error |

## Layout

```
source/textstat.d   pure counting over ubyte[], no IO
source/options.d    argv parsing, no side effects
source/runner.d     report building over an Io struct of function pointers
source/app.d        the only file that touches the real process
tests/              37 assertions in D, plus a shell parity suite against wc
```

## Testing

```sh
make test      # 37 assertions, no test framework
make parity    # diffs our output against wc across 6 inputs × 8 flag sets
```

The parity suite is the interesting one: it is what stops the counting code from
drifting away from `wc`, including the padding rules that decide whether a row
starts with a space.

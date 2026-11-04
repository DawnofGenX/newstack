# {{ project_name }}

{{ description }}

A command line tool written in [Standard ML](http://www.smlnj.org/sml97.html) and
compiled with [MLton](http://mlton.org/) into a single native binary. It counts
newlines, words and bytes exactly the way `wc` does — same figures, same column
widths, same exit codes — and proves it by diffing its output against the real `wc`.

## Requirements

- MLton 20210117 or newer (`apt-get install mlton` on Debian and Ubuntu)

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
 42  268 1731 README.md
$ ./bin/{{ npm_name }} README.md
 42  268 1731 README.md
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
src/counts.sml    pure counting over Word8Vector, no IO
src/options.sml   argv parsing, no side effects
src/runner.sml    report building over an io record, so tests can fake the disk
src/main.sml      the only file that touches the real process
app.mlb           the program's source list
tests.mlb         the test binary's source list
```

## Testing

```sh
make test      # 37 assertions in SML, no framework
make parity    # diffs our output against wc across 6 inputs × 8 flag sets
```

The parity suite is the interesting one: it is what stops the counting code from
drifting away from `wc`, including the padding rules that decide whether a row
starts with a space.

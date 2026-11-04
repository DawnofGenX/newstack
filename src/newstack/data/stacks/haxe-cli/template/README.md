# {{ project_name }}

{{ description }}

A command line tool written in [Haxe](https://haxe.org/) and compiled to Neko, so one
source tree runs on any machine with `haxe` and `neko` installed. It counts newlines,
words and bytes exactly the way `wc` does — same figures, same column widths, same exit
codes — and the shipped test suite proves that by diffing against the real `wc`.

## Requirements

- Haxe 4.3 or newer
- Neko 2.3 or newer (the runtime the program is compiled to)
- `make` (optional, but the workflows use it)

## Quick start

```sh
make build
./bin/{{ npm_name }} --help
./bin/{{ npm_name }} README.md
printf 'alpha beta\ngamma\n' | ./bin/{{ npm_name }}
```

`./bin/{{ npm_name }}` compiles the program the first time you run it, so `make build`
is a convenience rather than a requirement.

## What it does

```
$ wc README.md
  48  312 2048 README.md
$ ./bin/{{ npm_name }} README.md
  48  312 2048 README.md
```

`-l`, `-w` and `-c` (and the long forms `--lines`, `--words`, `--bytes`) select the
figures; they can be clustered (`-lw`). With no file, or with `-`, it reads standard
input. Two or more operands add a `total` row.

## Exit codes

| Code | Meaning |
| ---- | ------- |
| 0 | every operand was counted |
| 1 | at least one operand could not be read (the rest were still counted) |
| 2 | usage error, for example an unknown option |

## Layout

```
src/TextStat.hx   pure counting: lines, words, bytes
src/Options.hx    argv parsing, no side effects
src/Runner.hx     report building over an Io interface, so tests can fake the disk
src/Main.hx       the only file that touches the real process
tests/            43 assertions in Haxe, plus a shell parity suite against wc
```

## Testing

```sh
make test     # Haxe test binary: 43 assertions
make parity    # diffs our output against wc across 6 inputs × 8 flag sets
```

The parity suite is the interesting one: it is what stops the counting code from
drifting away from `wc`, including the padding rules that decide whether a row starts
with a space.

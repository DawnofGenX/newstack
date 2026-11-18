# {{ title }}

{{ description }}

Reflowing text is one of those jobs where the interesting part is not the greedy
fill loop but the decisions around it: which whitespace counts, what happens to a
word longer than the width, and whether running the tool twice changes the text.

## Layout

```
lib/wordwrap.rb        wrap() and the greedy reflow
lib/wordwrap/cli.rb    the command line, with the streams injected
bin/                   the executable
test/                  minitest: wrapping rules and CLI exit codes
```

## Usage

```console
$ printf 'one two three' | bin/{{ npm_name }} -w 7
one two
three
$ bin/{{ npm_name }} -w 40 README.md
```

`-w/--width` defaults to 76. With no `FILE` (or with `-`) the text comes from
standard input.

## The rules

| input | output |
| ----- | ------ |
| `one two three` at width 7 | `one two` / `three` (greedy fill) |
| `one two\nthree` at width 40 | `one two three` (a paragraph is reflowed) |
| `aaa\n\nbbb` | the blank line is a paragraph break and is preserved |
| `a\n\n\nb` | consecutive blank lines collapse to one |
| `short unbreakable` at width 5 | `short` / `unbreakable` (a long word is not split) |
| any text, wrapped twice | identical to wrapping it once |

That last rule is the reason newlines inside a paragraph are treated as spaces:
wrapping has to be idempotent or `fmt`-style pipelines keep changing the file.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | success, including `--help` |
| 1 | the named file cannot be read |
| 2 | usage error: a width below 1, an extra argument |

## Test

```console
$ rake test
$ bash smoke.sh
```

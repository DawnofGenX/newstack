# {{ title }}

A command line tool that counts newlines, words, and bytes, written in Scheme
on [GNU Guile](https://www.gnu.org/software/guile/). It is the `wc` classic,
narrowed to `-l`, `-w`, and `-c`, with a test suite that needs no framework.

## Run it

```console
$ {{ npm_name }} sample.txt
 2  4 23 sample.txt
$ printf 'alpha beta\ngamma\n' > sample.txt
$ {{ npm_name }} -w sample.txt
3 sample.txt
$ printf 'alpha beta\ngamma\n' | {{ npm_name }} -w
3
$ printf 'alpha beta\ngamma\n' | {{ npm_name }} -w -
3 -
```

The width of the columns follows `wc`: one figure from one readable operand is
not padded, a pipe gets the seven-wide cells, and the rest are as wide as the
byte total. A `total` row appears as soon as there is more than one operand,
even when one of them could not be read.

## Layout

```
main.scm                  the only file that touches a port or an exit code
lib/textstat/counts.scm   bytevector in, counts record out
lib/textstat/options.scm  argv in, a parsed record out
lib/textstat/runner.scm   the decision, with reading and writing injected
tests/                    a hand-written harness and three suites
```

Every module is a real Guile module, so each file states what it imports and
what it exports; the counting core never sees a port and the parser never sees
the terminal. `{{ npm_name }}` runs `guile --no-auto-compile -L lib -s main.scm`,
so there is no build step and nothing to compile first.

## Test

```console
$ ./bin/{{ npm_name }} --help
$ env GUILE_AUTO_COMPILE=0 guile --no-auto-compile -L lib -L tests -s tests/run-tests.scm
checks: 83, passed: 83, failed: 0
```

The suites feed the runner a record of four procedures, so a broken format
shows up without spawning a process, and the shipped `stdin` check is what
covers the real pipe path.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | everything asked for was counted |
| 1 | a file could not be read (the rest were still counted) |
| 2 | the arguments were wrong |

## Licence

MIT. See `LICENSE`.

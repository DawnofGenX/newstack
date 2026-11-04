# {{ npm_name }}

A Haskell CLI skeleton that counts lines, words and bytes the way `wc` does.
It is small on purpose: a pure counting core, a hand-written argument parser, a
runner behind a tiny `Io` record, and a test suite that needs nothing from
Hackage beyond `base` and `bytestring`.

```
$ printf 'alpha beta\ngamma\n' > sample.txt
$ printf 'delta\n' > second.txt
$ {{ npm_name }} sample.txt second.txt
 2  3 17 sample.txt
 1  1  6 second.txt
 3  4 23 total

$ {{ npm_name }} -w sample.txt
3 sample.txt

$ printf 'one line, no trailing newline' | {{ npm_name }} -c
29 -
```

## Layout

```
{{ cabal_name }}.cabal      cabal package: library, executable, test suite
app/Main.hs              the only module that touches files, terminals and exit codes
src/TextStat/Counts.hs   counting: bytes, words, newlines (pure)
src/TextStat/Options.hs  argv -> a decision (pure)
src/TextStat/Runner.hs   reads, prints, adds a total row, returns the exit code
test/Spec.hs             entry point of the test suite
test/Harness.hs          a 30-line harness: check, checkEqual, summary
test/*Spec.hs            counts, options and runner checks
bin/{{ npm_name }}       wrapper: builds incrementally, then execs the binary
```

## Requirements

GHC 9.4 and cabal-install 3.8 or newer. On Debian/Ubuntu:

```
sudo apt-get install -y ghc cabal-install
cabal update
```

`cabal update` is only needed so cabal has a package index to resolve against;
the project itself depends on `base` and `bytestring` alone, both of which ship
with GHC, so nothing is downloaded to build it.

## Quick start

```
cabal build all
cabal test all
./bin/{{ npm_name }} --help
```

## Behaviour worth knowing

- A line is a newline byte, so a final line without a trailing newline is not
  counted, exactly like `wc -l`.
- A word is a maximal run of non-whitespace bytes (space, tab, newline,
  vertical tab, form feed, carriage return).
- Bytes are counted from the raw input, so UTF-8 text counts two bytes per
  non-ASCII character.
- Columns are right-aligned to the widest figure in the output, and a `total`
  row is printed whenever more than one operand was named -- including when one
  of them could not be read, which is the case `wc` also prints a total for.
- With no FILE, or when FILE is `-`, the row is labelled `-`.

Exit codes: `0` success, also for `--help` and `--version`; `1` a file could not
be read (the other files are still reported); `2` a usage error.

## Why a hand-written test harness

The suite is 47 checks that print `ok name` or `FAIL name` and exit non-zero if
anything failed. That keeps the template dependency-free -- no tasty, no
hspec -- while still giving `cabal test` a real pass/fail signal. Swap in a
library when you outgrow it.

## License

MIT, see LICENSE.

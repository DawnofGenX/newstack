# {{ title }}

{{ description }}

encode(text) answers with a pair stream: one `(letter, count)` for
every run the stepper walks — runs of one kept as honest pairs,
never bare letters, stands longer than 255 split into consecutive
pairs of the same letter so the sum stays the length. decode(pairs)
replays every pair letter by letter and answers the text. The
promise is checked, never assumed: `decode(encode(text))` is the
text itself on every shipped and seeded corpus, and encode answers
exactly what the shipped stepper walks.

## Why

A counter earns trust the only way a counter can: its stream must
fold back to the letters it was sent, on every text — and a repeat
must cost strictly fewer pairs than letters. So this tool exists to
*show* that, not to state it:

```sh
$ {{ npm_name }} roundtrip abracadabraabracadabra
```

Every claim below is a comparison the selftest computes at run
time against the real modules, and `selftest` refuses to pass when
one stops holding. The falsifiable core is the loop: `naive.py`
prices every text at one pair per letter and collapses runs by
grouping, and every stream the counter emits must fold back to the
letters it was handed.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the loop closes | a read that loses letters | round-trip equal on shipped and seeded corpora |
| encode answers the stepper | a counter that invents runs | encode equals the stepper's walk on every text |
| the collapsed view is the walk | a walk that skips or repeats | pair letters in order equal the collapsed text |
| a repeat pays in pairs | a counter that never blinks | pair count strictly below letter count on repeats |
| the naive price is the ceiling | a counter worse than doing nothing | pairs never exceed one per letter |
| a capped stand stays whole | a count that eats letters | stands past 255 split, the sums stay exact |
| loud strings are refused | uppercase, digits, spaces | the gate names the string, no pair is emitted |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} encode "abracadabraabracadabra"
uv run {{ npm_name }} roundtrip "mississippimississippi"
uv run {{ npm_name }} report --corpus fixtures/corpora.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `encode TEXT` | the pair stream the counter pays for a text |
| `decode STREAM` | the letters a pair stream folds to |
| `roundtrip TEXT` | the loop, checked live before it answers |
| `report --corpus FILE` | a corpus counted, text after text |
| `demo` | six stories about runs, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

Texts are lowercase ASCII letters only; the empty text is legal,
up to 100,000 letters. `fixtures/corpora.txt` is one text per
line; blank lines and lines starting with `#` are skipped, and
every other line must pass the gate. A pair stream is a flat JSON
list of `[letter, count]` rows: `[["a", 3], ["b", 1]]` is three
`a`s then one `b`; counts run from 1 to 255.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the loop failed to close, a story fails |
| 2 | the input cannot be read: a loud string, a bad file |

## Files

```
src/{{ package_name }}/rle.py          the counter: encode, decode, the audit
src/{{ package_name }}/pairs.py        the pair, the stepper, and their JSON face
src/{{ package_name }}/text.py         the gate the strings pass
src/{{ package_name }}/naive.py        the one-pair-per-letter oracle
src/{{ package_name }}/corpus.py       text lists in, snapshots out
src/{{ package_name }}/demo.py         six stories, every claim computed
src/{{ package_name }}/cli.py          the command line
src/{{ package_name }}/selftest.py     the invariants, runnable in a checkout
fixtures/corpora.txt                   a corpus the smoke test builds on
smoke.sh                               the tool driven the way a user drives it
```

## Non-goals

No uppercase, no digits, no spaces, no Unicode beyond ASCII
letters, no general file compression, no alphabet coding, no
persisted storage, no streaming text. The counter is the honest
run-length it is: a tool for showing what a stepper promises a
loop, not a replacement for `zlib`.

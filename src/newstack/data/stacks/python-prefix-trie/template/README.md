# {{ title }}

{{ description }}

A prefix trie stores words as paths of single-letter branches: a word
ends where it is whole, at the node its last letter reaches, so no word
hides inside a longer one and no branch stands open on a word nobody
stored. Membership walks the letters; a prefix listing walks the open
branches under a stem in lexicographic order.

## Why

A trie earns trust the only way a query structure can: its answers must
equal a dumb scan's, on every corpus, after every delete. So this tool
exists to *show* that, not to state it:

```sh
$ {{ npm_name }} prefix --words fixtures/words.txt --prefix car
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one stops
holding. The falsifiable core is the scan: `scan.py` walks the corpus
with one comparison per word, and every membership and prefix answer
the trie returns must be the identical list, in the identical order.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| membership is a set's answer | a `has` that misses or invents a word | every seeded corpus in the selftest and the tests |
| a prefix listing is the sorted scan | a `prefix` out of lexicographic order | the scan comparison on every corpus |
| the empty prefix lists everything once | a word listed twice or never | `prefix("")` against `sorted(set(corpus))` |
| delete closes exactly one node | a survivor pruned with its stem | `audit()` and the survivor check after every delete |
| a rebuild reproduces every answer | insertion order leaking into an answer | tries built in opposite orders |
| the gate keeps letters out | an empty, uppercase, or letterless "word" | the word gate section |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} count --words fixtures/words.txt
uv run {{ npm_name }} has --words fixtures/words.txt cart
uv run {{ npm_name }} prefix --words fixtures/words.txt --prefix car
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `add --words FILE WORDS...` | store words, report what the trie holds after |
| `has --words FILE WORDS...` | membership, exactly |
| `prefix --words FILE [--prefix STEM]` | every word under a stem, in order |
| `delete --words FILE WORD` | drop one exact word, survivors keep their stems |
| `count --words FILE` | size and the stem every word shares |
| `demo` | six stories about letters and stems, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/words.txt` is one lowercase word per line, letters `a`-`z`
only, one to sixty-four of them. Blank lines and lines starting with
`#` are skipped. The empty stem asks for every word; a word that fails
the gate is refused by name, never quietly stored.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the word is not held, the stem lists nothing |
| 2 | the input cannot be read: a bad file, a bad word, a bad seed |

## Files

```
src/{{ package_name }}/trie.py       the branches, the words, the audit
src/{{ package_name }}/words.py      the gate the letters pass
src/{{ package_name }}/scan.py       the scan that is the oracle
src/{{ package_name }}/corpus.py     word lists in, snapshots out
src/{{ package_name }}/workload.py   seeded storms, re-checked per op
src/{{ package_name }}/demo.py       six stories, every claim computed
src/{{ package_name }}/cli.py        the command line
src/{{ package_name }}/selftest.py   the invariants, runnable in a checkout
fixtures/words.txt                   a corpus the smoke test builds on
smoke.sh                             the tool driven the way a user drives it
```

## Non-goals

No uppercase, no digits, no punctuation, no word past sixty-four
letters, no duplicate policy beyond "a word is stored once", no
persisted storage, no concurrent writers. The trie is the honest
letter-path structure it is: a tool for showing what branches buy a
dictionary, not a replacement for `set`.

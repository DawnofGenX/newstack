# {{ title }}

{{ description }}

build_tree(frequencies) answers with a deterministic ladder: the
two cheapest weights merge first, ties falling on the alphabet, a
fresh branch standing behind every older one. code_table deals the
ladder's depths into canonical bit strings — shortest words to the
heaviest letters, equal lengths in letter order — so encode spends
each letter its word and decode walks the wordlist alone. The
promise is checked, never assumed: the loop closes, no shipped code
opens where another closes, and a skewed text pays strictly under
eight bits a letter.

## Why

A coder earns trust the only way a coder can: its bits must read
back the letters they were sent, on every text — and a skewed text
must cost less than the eight bits a letter it replaces. So this
tool exists to *show* that, not to state it:

```sh
$ {{ npm_name }} roundtrip mississippimississippi
```

Every claim below is a comparison the selftest computes at run
time against the real modules, and `selftest` refuses to pass when
one stops holding. The falsifiable core is the loop:
`decode(encode(text), table) == text` on every shipped and seeded
corpus, and `audit(table)` walks the wordlist against itself —
one break and the tool says so.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the loop closes | a read that loses letters | round-trip equal on shipped and seeded corpora |
| no code prefixes another | an ambiguous wordlist | the audit walks every shipped pair |
| a skewed text pays under eight bits | a coder that never blinks | bits strictly below eight times letters on skewed fixtures |
| the ladder takes the two cheapest | a tree that guesses | first merge is a and b, never c, on {a:1, b:1, c:5} |
| ties fall alphabetically | a table that drifts | same weights, same ladder, any insertion order |
| the ladder and the table agree | a deal that invents depths | shipped words match harvested roads, prefix-free |
| the empty text spends nothing | a special case invented away | empty in, empty out, audit silent |
| loud strings are refused | uppercase, digits, spaces | the gate names the string, no bits are spent |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} encode "mississippimississippi"
uv run {{ npm_name }} roundtrip "abracadabraabracadabra"
uv run {{ npm_name }} report --corpus fixtures/corpora.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `encode TEXT` | the bit string the coder pays for a text |
| `decode BITS TEXT` | the letters a bit string reads back on a text's weights |
| `frequencies TEXT` | the weights the ladder is built from |
| `report --corpus FILE` | a corpus priced, text after text |
| `roundtrip TEXT` | the loop, checked live before it answers |
| `demo` | six stories about ladders and wordlists, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

Texts are lowercase ASCII letters only; the empty text is legal,
up to 100,000 letters. `fixtures/corpora.txt` is one text per
line; blank lines and lines starting with `#` are skipped, and
every other line must pass the gate. A table is a JSON object of
`letter -> bit string`; a wire message is `{"bits": ..., "codes":
...}` and reads back through the table alone.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the loop failed to close, a story fails |
| 2 | the input cannot be read: a loud string, a bad file |

## Files

```
src/{{ package_name }}/tree.py         the deterministic ladder, the walk, the harvest
src/{{ package_name }}/table.py        the canonical deal and the prefix-free audit
src/{{ package_name }}/coder.py        letters to bits, bits to letters, the ledger
src/{{ package_name }}/freq.py         the counts the ladder is built from
src/{{ package_name }}/text.py         the gate the strings pass
src/{{ package_name }}/corpus.py       text lists in, snapshots out
src/{{ package_name }}/workload.py     seeded storms, loop against loop
src/{{ package_name }}/demo.py         six stories, every claim computed
src/{{ package_name }}/cli.py          the command line
src/{{ package_name }}/selftest.py     the invariants, runnable in a checkout
fixtures/corpora.txt                   a corpus the smoke test builds on
smoke.sh                               the tool driven the way a user drives it
```

## Non-goals

No uppercase, no digits, no spaces, no Unicode beyond ASCII
letters, no file compression, no adaptive tables, no persisted
storage, no bit-level streaming protocol. The coder is the honest
canonical Huffman it is: a tool for showing what a deterministic
ladder promises a wordlist, not a replacement for `zlib`.

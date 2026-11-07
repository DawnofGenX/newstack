# {{ title }}

{{ description }}

compress(text) answers with a token stream: a literal writes one
letter, a back-reference quotes `length` letters sitting `offset`
places behind the end of the stream emitted so far — never further
than a 4096-letter window, never longer than 32 letters, never
into letters the window never saw. decompress replays each quote
letter by letter, so a quote may ride its own tail. The promise is
checked, never assumed: the loop closes, and every quote names
letters the reconstruction actually holds at that distance.

## Why

A coder earns trust the only way a coder can: its stream must read
back the letters it was sent, on every text — and a repeat must
cost fewer tokens than letters. So this tool exists to *show*
that, not to state it:

```sh
$ {{ npm_name }} roundtrip abracadabraabracadabra
```

Every claim below is a comparison the selftest computes at run
time against the real modules, and `selftest` refuses to pass when
one stops holding. The falsifiable core is the loop:
`naive.py` emits every letter as its own literal and replays
quotes one step at a time, and every stream the coder emits must
unfold back to the letters it was handed.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the loop closes | a read that loses letters | round-trip equal on shipped and seeded corpora |
| quotes name emitted letters | a quote into the unseen | the audit walks every token against the reconstruction |
| a repeat pays in tokens | a coder that never blinks | token count strictly below letter count on repeats |
| the naive price is the ceiling | a coder worse than doing nothing | tokens never exceed one per letter |
| a quote rides its own tail | a reader that cannot copy itself | offset-length quotes replay past the emitted end |
| the empty text streams empty | a special case invented away | empty in, empty out, audit silent |
| loud strings are refused | uppercase, digits, spaces | the gate names the string, no token is emitted |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} compress "abracadabraabracadabra"
uv run {{ npm_name }} roundtrip "mississippimississippi"
uv run {{ npm_name }} report --corpus fixtures/corpora.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `compress TEXT` | the token stream the coder pays for a text |
| `decompress STREAM` | the letters a token stream unfolds to |
| `roundtrip TEXT` | the loop, checked live before it answers |
| `report --corpus FILE` | a corpus priced, text after text |
| `demo` | six stories about windows, with real numbers |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

Texts are lowercase ASCII letters only; the empty text is legal,
up to 100,000 letters. `fixtures/corpora.txt` is one text per
line; blank lines and lines starting with `#` are skipped, and
every other line must pass the gate. A token stream is a flat JSON
list: `["a", "r"]` is a literal, `["b", 4, 9]` quotes nine letters
from four back.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the invariants hold |
| 1 | the loop failed to close, a story fails |
| 2 | the input cannot be read: a loud string, a bad file |

## Files

```
src/{{ package_name }}/coder.py        the window, the scan, the loop, the audit
src/{{ package_name }}/tokens.py       literals, back-references, and their JSON face
src/{{ package_name }}/text.py         the gate the strings pass
src/{{ package_name }}/naive.py        the literal-only coder that is the oracle
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
letters, no general file compression, no entropy coding, no
persisted storage, no streaming text. The coder is the honest
LZ77 it is: a tool for showing what a sliding window promises a
loop, not a replacement for `zlib`.

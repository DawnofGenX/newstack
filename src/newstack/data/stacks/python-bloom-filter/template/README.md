# {{ title }}

{{ description }}

A Bloom filter with nothing to hide: a documented bit-array over the
universe `[0, 256)`, k deterministic multiplicative rows per key —
the count-min family's arithmetic, `h_i(x) = (x + 1) · A_i mod (2⁶¹−1)
mod width` with every `A_i` odd — and one promise the shipped audit
re-counts on every run: a key added is *always* answered present.
False negatives are not tolerated, they are measured: every shipped
config re-asks every added key after every update on five seeded
streams, 7920 re-asks, zero misses.

The other half is the honest edge, and the docs refuse to round it
off: a *yes* can be another key's seating standing in for its own.
At the shipped widths (1024 and 2048 bits, 4 rows) no absent key
answers present on the shipped streams — the survey lists the liars
and the list is empty, list in hand. Shrink the array and the liars
come back; that is arithmetic, not a bug, and `demo` shows a 64-bit
array answering present to absent keys on purpose. Removal is not on
the menu: clearing an item's rows erases whatever else shares those
bits.

Same seed, same answers: every stream is `random.Random(seed)` and
every row is plain multiply-and-fold, so a replay on a fresh checkout
raises the same bits forever.

## The rules

| rule | forbids | proved |
| --- | --- | --- |
| no false negatives | an added key answered absent | `Bloom.audit()` re-asks every added key; `shipped_audit()` re-asks every key after every update, 7920 re-asks, 0 breaks |
| the edge is one-way | a *no* that lies | `might_contain` answers no only on a row never raised; `survey()` lists the keys that lie *present* — empty at the shipped widths |
| no removal | clearing a shared row | `add` only raises bits; erasing would unseat every co-tenant, so the API has no delete |
| the gate is the domain | anything outside `[0, 256)` | `ensure_key` rejects negatives, 256, floats, booleans; `parse_key` rejects non-digits |
| deterministic rows | digest drift, call-time randomness | `multiplier(row, seed)` is odd arithmetic; `rows_for` replays bit-for-bit |
| same seed, same answers | a stream that drifts | `stream(seed)` replays; the fixture freezes five streams and the selftest re-derives them |
| the shape is documented | a runaway array | width ∈ [8, 65536], rows ∈ [1, 16], default 1024×4, seed 11 |

## Quickstart

```bash
uv sync
uv run {{ npm_name }} add --key 7 --key 42
uv run {{ npm_name }} check 165          # exit 0: present
uv run {{ npm_name }} check 1            # exit 1: absent
uv run {{ npm_name }} report             # the shipped audit, counted
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | answers | exit codes |
| --- | --- | --- |
| `add --key K [--key K] [--width W] [--rows R] [--seat S]` | seat keys in a fresh array | 0 |
| `check K [--seed S]` | ask one key of the seeded filter | 0 present, 1 absent |
| `report` | the shipped audit: re-asks, liars, estimate | 0 clean, 1 broken |
| `seed N [--length L]` | the stream one seed draws, replayed | 0 identical, 1 diverged |
| `selftest` | every invariant, run against the modules | 0 clean, 1 failures |
| `demo` | the claims, computed live | 0 all hold |

`--json` rides on `add`, `check`, `report`, and `seed`.

## Exit codes

| code | meaning |
| --- | --- |
| 0 | present, clean, or a usable run |
| 1 | absent, or an audit that broke |
| 2 | the arguments or the file cannot be used as given |

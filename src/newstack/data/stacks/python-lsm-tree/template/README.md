# {{ title }}

{{ description }}

A log-structured merge table keeps recent writes in a sorted in-memory
memtable and freezes it, whole, into numbered level tables on disk as soon
as the limit bites. A read checks the memtable first and then falls
through the level tables newest-first, stopping at the first table that
knows the key; a tombstone outranks the value it buries, in the memtable,
in a level file, and after a reopen. Compaction merges every level table
into one sorted table and retires the tombstones, because after a full
merge nothing older is left to hide.

## Why

An LSM table earns trust at the flush boundary, not in a comment. So this
tool exists to *show* that, not to state it:

```
$ {{ npm_name }} workload --seed 7 --limit 3 --dir .table
```

Every claim below is a comparison the selftest computes at run time against
the real modules and a plain dict, and `selftest` refuses to pass when one
stops holding. The falsifiable core: a seeded write/delete/read workload
under a memtable limit of one forces a flush per write, and every key's
final answer equals the dict answer — many flushes, many levels, one truth.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the dict is the answer | a workload whose final answers differ from a plain dict | every seeded replay in the selftest, limits 1 and 3 |
| a tombstone outranks the value it buries | a deleted key answering with an older value | the tombstone and fall-through tests |
| reads fall through, newest first | a read that stops at the memtable or at the oldest level | the level fall-through tests |
| iteration is sorted-unique | a duplicated or unsorted key across levels | the walk against `sorted` on every replay |
| compaction drops tombstones | a tombstone surviving a full merge | the merge tests, before and after |
| reopen reads the identical table | a directory whose answers drift | reopen against the pre-flush answers |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} workload --seed 7 --limit 3 --dir .table
uv run {{ npm_name }} put --dir .table --key 12 --value alpha
uv run {{ npm_name }} get --dir .table --key 12
uv run {{ npm_name }} compact --dir .table
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `put --dir DIR --key N --value TEXT` | write one key into the memtable |
| `get --dir DIR --key N [--json]` | one key, memtable then levels, newest first |
| `delete --dir DIR --key N` | bury a key under a tombstone |
| `load --dir DIR --ops FILE [--json]` | replay an op file into the table |
| `flush --dir DIR [--json]` | freeze the memtable into the next level |
| `compact --dir DIR [--json]` | merge every level, drop every tombstone |
| `workload --dir DIR [--seed N] [--limit N] [--json]` | a seeded mix, answered against a dict |
| `demo` | the six stories, computed live |
| `selftest` | the invariants, runnable in a fresh checkout |

## Input format

`fixtures/ops.txt` is one op per line: `put N text`, `del N`, or `get N`.
Blank lines and lines starting with `#` are skipped. A level table on disk
is `<seq>.lsm`, six digits of birth order, one `key<TAB>value` record per
line, an empty value standing for a tombstone.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was found, or the invariants hold |
| 1 | the key is absent, the window empty, or an invariant failed |
| 2 | the input cannot be read: a bad file, a bad key, a bad limit |

## Files

```
src/{{ package_name }}/table.py       the memtable, the levels, the fall-through
src/{{ package_name }}/levels.py      frozen level tables, sorted, numbered
src/{{ package_name }}/ops.py         workload streams and the dict they answer to
src/{{ package_name }}/demo.py        the six stories, computed live
src/{{ package_name }}/cli.py         the command line
src/{{ package_name }}/selftest.py    the invariants, runnable in a fresh checkout
fixtures/ops.txt                      a stream the smoke test replays
smoke.sh                              the tool driven the way a user drives it
```

## Non-goals

No string keys, no values over a tab, no write-ahead log, no concurrent
writers, no leveled compaction strategy beyond full merge, no real crash
test. This is a tool for showing where an LSM table keeps its promises —
across the flush boundary and a reopen — not a database.

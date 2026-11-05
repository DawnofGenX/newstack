# {{ title }}

An append-only log whose tampering is detectable — and whose detection is tested.

Every event also carries a hash over its canonical body and points at the hash of the event before
it, so an edit, a deletion, or a reordering shows up. That is the easy half. The hard half is the
attack a hash chain cannot see: someone with write access recomputes every hash and the chain
looks perfect. Only a checkpoint kept somewhere else catches that, so this stack ships one, tests
it, and makes `demo` exit non-zero when that scenario is missed.

```
$ {{ npm_name }} --db audit.db append --actor alice --action note.update --target note/1 \
      --detail field=title
seq 1  hash fce8d245ee6b298bda52fe0e40f45f12b90f1260d4755b58e1703094ef21c801
  at      2026-11-05T20:14:03.074333+00:00
  actor   alice
  action  note.update
  target  note/1
  detail  {"field":"title"}
  prev    0000000000000000000000000000000000000000000000000000000000000000
  hash    fce8d245ee6b298bda52fe0e40f45f12b90f1260d4755b58e1703094ef21c801
```

## Why this exists

"Audit log" usually means a table with a timestamp and a `who` column. It answers nothing when the
question is *was this log changed?* — the log's owner can edit a row and the edit looks like every
other row. A hash chain is the cheapest way to make that question answerable, as long as you know
exactly what it does not cover.

## Quick start

```
uv venv
uv pip install -e . pytest ruff

{{ npm_name }} append --actor alice --action note.update --target note/1
{{ npm_name }} list
{{ npm_name }} verify
{{ npm_name }} checkpoint --out /somewhere/else/head.json
{{ npm_name }} demo
PY=.venv/bin/python bash smoke.sh
```

## The five scenarios `demo` runs

```
$ {{ npm_name }} demo
nothing (a clean log)          caught  every link recomputes to its stored hash
    verify  ok: 3 event(s), head 3 624aeaf44c6244ef…, every link recomputed

edit one row, keep its hash    caught  the body no longer hashes to the stored hash
    verify  FAILED: 1 problem(s) in 3 event(s)
    seq    2  body-changed  stored hash 647ab3c29c886403… but the body now hashes to 68ceac35a9a5786b…

delete a row                   caught  the sequence numbers stop being contiguous
    verify  FAILED: 2 problem(s) in 2 event(s)
    seq    3  gap           expected seq 2, found 3
    seq    3  chain-broken  prev_hash 7e39ac3d54b72b40… is not the previous event's 6aed6d70a90c9529…

recompute every hash           MISSED  a chain is a checksum, so this looks clean
    verify  ok: 3 event(s), head 3 2c0eb8ed3094e42a…, every link recomputed

recompute every hash, with a checkpoint caught  the remembered head is the evidence
    verify  FAILED: 1 problem(s) in 3 event(s)
    seq    3  rewritten     the checkpoint has d4cabe908296c0aa… at seq 3, the log has 2c0eb8ed3094e42a…

demo: 5 scenarios, 1 missed
```

The last line is the point: `demo` exits `1` while any scenario is missed, so a change that quietly
breaks the checkpoint gate fails the smoke test instead of shipping.

## Exit codes

| code | meaning |
| --- | --- |
| 0 | the command did what it said |
| 1 | the log is broken (`verify` found a problem) or `demo` missed a scenario |
| 2 | the request was unusable: bad flag, unreadable checkpoint, non-JSON value |

## The traps

1. **A hash chain is a checksum, not a signature.** Anyone who can write the file can recompute
   every hash. The chain proves accidental corruption and casual edits, not a determined attacker.
   A checkpoint outside the log's trust boundary is what upgrades it; an HMAC keyed with something
   the writer does not have is what upgrades it further.
2. **An edit is caught at its own row, and only there.** Editing a body while leaving the `hash`
   column alone does not break the *next* event's link — that link points at the stored hash, which
   is unchanged. A chain proves the links; the links alone never prove the prose.
3. **A head checkpoint is a bound, not a copy.** It remembers the count and the head hash, so it
   catches truncation and a full rewrite. An edit *below* the head is the chain's job, not the
   checkpoint's. Saying "a checkpoint catches everything" would be a lie you would discover in an
   incident review.
4. **The timestamp is not the order.** Clocks go backwards, machines disagree, NTP steps. `seq` is
   the order, `at` is trivia — `list` sorts by `seq` for exactly that reason.
5. **Floats are refused, not rounded.** `1.0` prints as `"1.0"` in Python and `"1"` in JavaScript,
   so two verifiers would disagree about the same event and both would call themselves right. Store
   minor units as an int, or the ratio as a string.
6. **Canonical form is why key order and whitespace are free.** The hash covers
   `json.dumps(sort_keys=True, separators=(",", ":"))`, so a database that reorders keys, or a tool
   that pretty-prints, does not break the chain — only the values matter.
7. **The checkpoint must live where the log's owner cannot write.** Next to the database it is
   decoration: whoever rewrites the chain rewrites the checkpoint too.
8. **`--detail k=v` cannot type a value.** Everything from the shell is a string, so `attempts=3`
   records `"3"`. `--detail-json '{"attempts": 3}'` is how a value keeps its type, and the CLI
   refuses the two forms disagreeing about the same key.
9. **An empty log verifies.** Zero events is a valid chain; refusing it would make a fresh install
   look broken.
10. **`BEGIN IMMEDIATE`, not `BEGIN`.** The write lock has to be taken *before* the read that picks
    the next sequence number, or two writers mint the same number and the chain forks.

## Layout

| path | what lives there |
| --- | --- |
| `src/{{ package_name }}/canon.py` | canonical JSON, the float refusal, the digest |
| `src/{{ package_name }}/record.py` | one event: the body the hash covers, and the hash |
| `src/{{ package_name }}/store.py` | the SQLite table, `BEGIN IMMEDIATE`, append and read |
| `src/{{ package_name }}/verify.py` | the chain check, checkpoints, the problem kinds |
| `src/{{ package_name }}/demo.py` | the five scenarios, run against throwaway databases |
| `src/{{ package_name }}/cli.py` | `append`, `list`, `verify`, `checkpoint`, `demo`, `selftest` |
| `src/{{ package_name }}/selftest.py` | the checks behind `selftest` |

## Tests

```
{{ npm_name }} selftest        # no pytest needed, installs nothing
.venv/bin/python -m pytest     # 65 tests
```

The interesting test is
`tests/test_verify.py::test_a_full_rewrite_beats_the_chain_and_loses_to_the_checkpoint`: it rebuilds
every hash and asserts the bare chain *passes*, then asserts the checkpoint fails it. A test that
only checked the failure would pass even if the chain check were broken.

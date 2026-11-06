# {{ title }}

{{ description }}

Four cache replacement policies, one trace generator, one number that makes the
comparison honest: the ceiling. Every table in this README was produced by running
the command shown above it.

## The rules this package keeps

1. **The trace is generated from a seed.** A hit ratio is only worth publishing if
   the next person can regenerate the traffic that produced it. `--seed` is part of
   the input, not a detail.
2. **No policy can beat the ceiling.** The ceiling is the share of accesses that go
   to the `capacity` most used keys: the best any policy could do with perfect
   knowledge of the future. Every table prints it, so "0.58" is read as
   "0.58 of a possible 0.70" rather than as a score.
3. **The work is counted, not assumed.** Evictions are counted for every policy, and
   the two policies that do extra work count it: CLOCK counts the slots it sweeps,
   SLRU counts the promotions it performs. A hit ratio bought with unbounded work is
   not a result.
4. **A loop that does not fit is zero for everybody.** With 200 keys and room for
   150, every policy scores 0.0000. Capacity is the lever; policy is the fine print.
   This is the story a benchmark usually leaves out.
5. **The ranking is a property of the trace, not of the policy.** SLRU beats LRU by
   more than a third on a sequential scan and loses to it on a mixed trace. Quoting
   "SLRU is better" without the trace is quoting half a measurement.
6. **A threshold is an exit code.** `--min-hit-rate` turns a table into a gate, so a
   capacity decision can be enforced by a build instead of a review comment.
7. **Refusals are named.** An unknown policy lists the policies that exist, an
   unknown trace lists the traces that exist, and a capacity below one is refused
   instead of silently simulating a cache that holds nothing.

## What it looks like

```console
$ {{ npm_name }} compare --trace zipf --accesses 20000
trace        zipf - 1/rank popularity over 1000 keys, so a few keys carry most of the traffic
capacity     100, ceiling 0.6996
policy capacity   hit rate     hits evictions    scans promotions
fifo        100     0.5261    10521      9379        0          0
lru         100     0.5813    11625      8275        0          0
clock       100     0.5674    11347      8553    20432          0
slru        100     0.6534    13068      6832        0        676
best         slru at 0.6534, 0.0462 under the ceiling
```

CLOCK reaches within 1.4 points of LRU while doing its work as sweeps instead of
list moves; SLRU buys 7 points over LRU by keeping a protected set.

The scan trace is where the policies separate:

```console
$ {{ npm_name }} simulate --policy slru --trace scan --accesses 20000
trace        scan - half a hot working set, half a sequential sweep that is never reused
accesses     20000 over 9910 distinct key(s)
policy capacity   hit rate     hits evictions    scans promotions
slru        100     0.5035    10070      9830        0         50
ceiling      0.5095
```

SLRU lands within 0.006 of the ceiling on a trace with a scan in it, because the
sweep only ever fills its probation area. LRU scores 0.3679 on the same trace.

Capacity, not policy, is what the curve says:

```console
$ {{ npm_name }} curve --capacities 10,25,50,100,200,400 --accesses 20000
trace        zipf - 1/rank popularity over 1000 keys, so a few keys carry most of the traffic
policy       lru
capacity   hit rate   ceiling
      10     0.2100    0.3931
      25     0.3532    0.5160
      50     0.4681    0.6055
     100     0.5813    0.6996
     200     0.7014    0.7944
     400     0.8205    0.8897
```

Four times the capacity is worth more than any of the four policies is worth to each
other, and the ceiling rises with it, so the gap to perfect knowledge stays roughly
constant in points rather than shrinking.

## The six demo stories

`{{ npm_name }} demo` measures the six claims in order and prints `-> holds` after
each one. They are written so that a regression in the library breaks the demo, not
just the test suite:

| story | claim |
| --- | --- |
| 1 | a popularity trace rewards remembering what was used |
| 2 | a loop that does not fit is zero for every policy, and 0.99 when it fits |
| 3 | a sequential scan erases an LRU while a segmented cache survives it |
| 4 | CLOCK buys most of LRU for a sweep instead of a reorder |
| 5 | capacity decides more than policy does |
| 6 | the trace decides the ranking, so the winner is not a constant |

## Exit codes

| code | meaning |
| --- | --- |
| 0 | the run finished and any gate passed |
| 1 | the run finished and a gate failed (`--min-hit-rate` with `simulate`/`compare`) |
| 2 | the request could not be answered: unknown policy or trace, unreadable capacity, zero capacity |

## Layout

```
src/{{ package_name }}/
  cache.py      fifo, lru, clock, slru - the bookkeeping, and what each one counts
  trace.py      zipf, loop, scan, mixed - generated from a seed
  rng.py        SplitMix64, so a published trace is the same on every interpreter
  simulate.py   run, compare, ceiling, capacity_curve, winner
  demo.py       the six stories
  cli.py        simulate, compare, curve, demo, selftest
  selftest.py   the rules above, as in-process checks
```

## What this package does not do

It does not store values, so it measures admission and eviction, not memory layout or
lookup cost. It does not model write-back, TTLs, or per-key sizes: every access costs
the same and every key occupies one slot. The traces are synthetic on purpose - a real
trace would make the numbers unreproducible without shipping the trace, so the shapes
are named instead (`zipf`, `loop`, `scan`, `mixed`) and the seed is part of the input.

## Quick start

```console
uv venv --python 3.12
uv pip install -e . pytest ruff
.venv/bin/python -m {{ package_name }} demo
.venv/bin/python -m pytest -q
PY=.venv/bin/python bash smoke.sh
```

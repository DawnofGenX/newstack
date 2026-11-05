# {{ title }}

Wall time that never runs backwards, and a stamp you can sort.

{{ description }}

## Why a wall clock is not enough

Two machines' wall clocks disagree. One is stepped back by NTP. A VM is paused
for 400 ms and resumes with a clock that is behind the message it just sent.
Every one of those events turns "sort by timestamp" into a guess, and a guess
is how a ledger ends up with a receipt before the message that caused it.

A hybrid logical clock (HLC) keeps a physical component that tracks the wall
when the wall is sane, and a logical counter that does the ordering when the
wall cannot be trusted. The result is a stamp that never goes backwards and
never puts a message before its send.

## The rules this project keeps

1. **A wall clock that steps backwards cannot move a stamp.** The stamp keeps
   the highest physical millisecond it has ever issued; the counter breaks the
   tie inside that millisecond.
2. **A message cannot arrive before it was sent.** Receiving a stamp later than
   the local clock moves the local clock past the received one, whatever the
   wall says.
3. **Skew is a number, not a feeling.** `physical_ms - wall_ms` is reported per
   node, and an optional bound turns an over-large skew into a refusal instead
   of a silent wrong answer.
4. **The node name makes the order total.** Two events in the same millisecond
   with the same counter still sort consistently, because the node name is part
   of the key — and the text form sorts the same way as the key.
5. **The wall order is recorded, not trusted.** The audit compares the wall
   order with the stamp order and prints the inversions; it does not hide them.
6. **A plan is replayable.** The same events against the same start time
   produce the same stamps, so a disagreement can be reproduced rather than
   argued about.

## Try it

```console
$ {{ npm_name }} demo
1. a wall clock that steps backwards cannot move a stamp
  wall 1700000000000                 -> 000001700000000000:0000000@a
  wall 1699999999600 (stepped back) -> 000001700000000000:0000001@a
  wall 1699999999600 (again)        -> 000001700000000000:0000002@a
  the stamps still increase: True
  the counter carried the order: 1 then 2
  -> holds

2. a message cannot arrive before it was sent
  a runs 500 ms fast: its wall reads 1700000000500
  b's wall reads 1700000000000, so on the wall the receipt came first
  send    000001700000000500:0000000@a
  receive 000001700000000500:0000001@b
  the receipt is later by stamp: True
  -> holds

3. the wall order and the stamp order disagree
  wall order:
    local   b wall 1700000000000
    receive b wall 1700000000000
    local   b wall 1700000000000
    send    a wall 1700000000500
  stamp order:
    local   b 000001700000000000:0000000@b
    send    a 000001700000000500:0000000@a
    receive b 000001700000000500:0000001@b
    local   b 000001700000000500:0000002@b
  inversions between the two orders: 2
  causal breaks under the stamp order: 0
  -> holds
```

Story 3 is the one to read twice: sorted by wall time the `send` comes last,
sorted by stamp it comes before its own receipt. The two orders disagree, and
only one of them is consistent with causality.

The remaining three stories check the total order, the skew bound, and a
three-node exchange; run `{{ npm_name }} demo` to see them.

## A plan you can replay

Plans are JSONL, one event per line, so a disagreement has a file:

```console
$ {{ npm_name }} plan --plan fixtures/handoff.jsonl
stamps
  local     b        000001700000000000:0000000@b  order placed
  send      a        000001700000000500:0000000@a  -> b ping
  receive   b        000001700000000500:0000001@b  <- a
  local     a        000001700000000505:0000000@a  settled
report
  node             physical_ms  logical             wall_ms  skew_ms
  a              1700000000505        0       1700000000505        0
  b              1700000000500        1       1700000000005      495
coverage
  a        events 2    receipts 0    wall jumps 2   skew 0 ms
  b        events 1    receipts 1    wall jumps 1   skew 495 ms
messages     1
causal breaks 0
```

`b`'s wall clock is 495 ms behind its physical clock here: the receipt dragged
it forward to what `a` had already seen. Nothing was broken — the report simply
says so, in numbers.

Event types: `offset`, `local`, `send`, `tick`, `back`.

```console
$ {{ npm_name }} plan --plan fixtures/handoff.jsonl --max-skew 100
...
skew         495 ms is past the 100 ms bound
$ echo $?
1
```

## Use it in code

```python
from {{ package_name }}.clock import HybridClock
from {{ package_name }}.world import World

clock = HybridClock("orders", wall_ms=lambda: 1_700_000_000_000, max_skew_ms=500)
first = clock.now()
received = clock.receive(remote_stamp)      # later than both, always
clock.check_skew()                          # raises if the wall is the broken one
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the command held its contract |
| 1 | a plan broke causality, or a skew passed the bound |
| 2 | the input could not be read or parsed — nothing was decided |

`{{ npm_name }} stamp <text>` reads a stamp back into `(physical_ms, logical,
node)`, which is the quickest way to answer "which of these two came first?".

## Layout

```
src/{{ package_name }}/
  stamp.py      the stamp, its text form, and its order
  clock.py      the hybrid clock, the manual wall, and the skew bound
  world.py      a set of nodes with offsets, driving plans
  plan.py       loading and executing JSONL events
  audit.py      the two orders, the inversions, the causal breaks
  demo.py       the six stories
  cli.py        plan / stamp / demo / selftest
tests/          pytest, one file per module
fixtures/       handoff.jsonl, step-back.jsonl
```

## Verify it yourself

```console
$ uv venv
$ uv pip install -e . pytest ruff
$ .venv/bin/pytest -q
$ .venv/bin/ruff check .
$ .venv/bin/python -m {{ package_name }} selftest
$ bash smoke.sh
```

## What this project does not do

- It does not synchronise clocks. NTP exists; this is about what to do while
  clocks disagree.
- It does not store history. Ordering is provided; durability is your store's
  problem.
- The physical component is a millisecond counter, not a proof of time. A clock
  pushed years into the future by a bad VM snapshot will drag its peers forward
  — which is exactly why `--max-skew` exists.

## License

MIT. See LICENSE.

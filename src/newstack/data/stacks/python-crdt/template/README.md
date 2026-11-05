# {{ title }}

{{ description }}

`{{ npm_name }}` merges replicated state and shows what each merge guarantees: the three laws
are checked on real states, and a shuffled, duplicated gossip run is what proves the replicas
agree. Nothing here reads a wall clock to decide an order it cannot know.

## The rules these replicas keep

1. **A merge is a join, or it is not a merge.** Every type is checked for idempotence
   (`merge(x, x) = x`), commutativity (`merge(a, b) = merge(b, a)`) and associativity — over
   every state and pair the suite has, not by assertion in a comment.
2. **Never merge signed counts with `max`.** `max` keeps the higher number, so a delayed copy
   of a node that decremented reads as *newer* and the decrement disappears. A grow-only
   counter per direction (`PNCounter` = positive minus negative) has no such reading.
3. **A counter belongs to a node.** Each replica owns its own entry; `merge` takes the highest
   count per node. Two increments from one node cannot cancel, because they are the same entry.
4. **Last-write-wins is a decision, not a merge.** `LWWRegister` orders writes by
   `(millisecond, node name)`, so the outcome is deterministic — and it silently drops the
   write that lost. The `Write` record says which stamp was dropped, so the loss can be
   reported instead of hidden. Two different values under one stamp are refused: a stamp is
   supposed to identify exactly one write.
5. **A remove is an observation, not a verdict.** `ORSet` gives every add a unique
   `(node, counter)` tag; `remove` only deletes the tags it has seen. An add that happened
   somewhere else survives, which is why the set is add-wins rather than "the last message
   wins" (that version, `PlainSet`, is included to be shown failing).
6. **Tombstones are kept, not garbage collected.** The set of removed tags only grows, which is
   exactly what makes the merge idempotent. Re-adding after a remove creates a fresh tag, so the
   element comes back — deliberately.
7. **Convergence is proven by delivery you did not choose.** `gossip` shuffles the order, sends
   every message twice, and repeats for several rounds; a merge that needs a total order fails
   that, and the report says so.

## Quickstart

```console
$ uv venv --allow-existing .venv
$ uv pip install --python .venv/bin/python -e . pytest ruff
$ .venv/bin/python -m {{ package_name }} demo
```

```text
1. a counter merged by max cannot subtract
  node a decremented twice; a copy from before the second decrement arrives late
  the older copy    a=-1
  the newer copy    a=-2
  merged by max     -1
  max() keeps the higher number, so it read the newer copy as the older one
  a grow-only pair survives this: the decrements land in different counters

3. a last-write-wins register drops a concurrent write
  both replicas wrote in the same millisecond, 1000
  replica a wrote red, replica b wrote blue, neither saw the other
  merged value      'blue', stamp 1000@b
  the write from a is gone, and the register cannot even report that it went
  the node name is the tiebreak, so the choice is deterministic rather than fair

5. an observed-remove set keeps the add it never saw
  replica a added x and then removed it; replica b added x at the same time
  a alone           present = False
  merged            present = True  tags [('b', 1)]
  remove again      present = False, having now seen every tag
  add wins, because each remove only ever deletes the tags it has observed
```

`{{ npm_name }} laws` runs the three laws against every type and exits non-zero if one breaks:
a merge that keeps the left argument breaks commutativity, and an averaging merge breaks
associativity — both are in the suite, so the checker itself is checked.

## Merging two states

```console
$ {{ npm_name }} merge fixtures/counter-a.json fixtures/counter-b.json
{
  "counts": {
    "a": 2,
    "b": 3
  },
  "type": "g-counter"
}
```

`merge` refuses two states of different types: a `g-counter` and an `or-set` are different
lattices, and there is no answer to "what is their join".

| Type | `merge` is | Refuses |
| --- | --- | --- |
| `g-counter` | pointwise max per node | a negative or non-integer stored count |
| `pn-counter` | max of each half | a negative stored half |
| `lww-register` | the higher `(ms, node)` stamp | two values under one stamp |
| `or-set` | union of tags and tombstones | a malformed tag |

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | the command did what was asked |
| `1` | a law did not hold (only `laws` returns this) |
| `2` | the arguments or a state file cannot be used as given |

## What this stack does not do

No anti-entropy protocol, no delta-state replication, no operation log, no causal delivery.
Those are transport decisions. What is here is the part that has to be right first: the merge
function, and the proof that merging in any order any number of times reaches the same state.

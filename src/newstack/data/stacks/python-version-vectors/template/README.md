# {{ title }}

{{ description }}

A version vector is one counter per writer. Comparing two of them gives one of four
answers - **equal**, **before**, **after**, **concurrent** - and every replica gives
the same answer for the same pair, because the answer is a property of the data and not
of who asked. That is the whole point: a total order can be different on two replicas
for the same two events, while a vector gives one verdict everywhere.

```
$ {{ npm_name }} compare --left a:2,b:1 --right b:4
left         a:2,b:1
right        b:4
relation     concurrent
why          concurrent: b is ahead on the right; a is ahead on the left
concurrent   neither write saw the other, so a rule has to pick one
```

## The rules this package keeps

1. **A comparison is a partial order, not a clock.** `before`, `after` and `equal` are
   transitive; `concurrent` means neither side saw the other, and no rule in this
   package invents an order for it. A caller that needs a total order (a last write,
   a tie break) has to bring one and say so.
2. **A merge is a join.** `merge` is the pointwise maximum: idempotent, commutative and
   associative, so the order replicas exchange state in cannot change the result, and a
   duplicate delivery changes nothing.
3. **A message carries the sender's state at send time.** Causal delivery then asks one
   question - "do I already hold everything this message depends on?" - and the answer
   is a comparison of vectors, not a guess about clocks or arrival order.
4. **A message that is not ready waits.** It is held, and delivered when the arrival of
   something else makes it ready. The ungated replica in the demo exists to show that
   the gate is doing work: without it, the reply is delivered before the message it
   answers, and the count of causality breaks goes from 0 to 1.
5. **Compaction is sound above the floor and lossy below it.** The floor is the
   pointwise minimum of the vectors a system still cares about. Dropping the counters
   that sit at the floor is exact for vectors that dominate it, and it is not exact for
   vectors that do not - the demo measures both halves of that sentence.
6. **Width is a cost, and it is reported.** The text form sorts its entries, so two equal
   vectors print identically and a diff of two text forms is meaningful.
7. **Nothing here hides a verdict.** `compare` exits 1 when the answer is
   `concurrent`, `prune` exits 1 when the vector is below the floor, and `pairs` exits 1
   when any pair in a file is concurrent - the exit code is how a script gates on it.

## What the demo measures

```
$ {{ npm_name }} demo
1. a Lamport order is total, and the order is an artifact
  the two replicas never exchanged a message, so both events are concurrent
  idle replica  0001@b then 0003@a
  busy replica  0003@a then 0006@b
  five unrelated local events were enough to put the comment on the other side
  -> holds

2. a version vector refuses to order them
  left         a:1
  right        b:1
  relation     concurrent
  why          concurrent: b is ahead on the right; a is ahead on the left
  lamport says 0001@a before 0001@b
  after merge  a:1,b:1, which is after both
  -> holds

3. the merge is a join, so order and repetition do not matter
  vectors      a:2,b:1 , b:3,c:1 , a:1,c:4
  merged       a:2,b:3,c:4
  idempotent   True
  commutative  True
  associative  True
  reversed     a:2,b:3,c:4, which is the same vector: True
  -> holds

4. causal delivery holds a message it cannot yet deliver
  no gate      delivered ['m2', 'm1']
  breaks       1: m2 b->c needed a at 1, had 0
  gated        m2 was held, 1 held
  then         m1 was delivered, releasing ['m2']
  delivered    ['m1', 'm2']
  breaks       0
  -> holds

5. compaction is exact above the floor and lossy below it
  floor        a:3,b:2,c:1
  vectors      7, pairs 21
  above floor  6 pair(s), 0 verdict(s) changed
  below floor  15 pair(s), 6 verdict(s) changed
  sound above  yes
  changed      a:3,b:2,c:1 vs a:0,b:1,c:1: after became equal
  changed      a:3,b:2,c:1 vs a:1,b:1,c:1: after became equal
  changed      a:3,b:2,c:1 vs a:2,b:0,c:1: after became equal
  -> holds

6. the width is the number of writers still being tracked
  full         w0:1,w1:2,w2:3,w3:4,w4:5,w5:6,w6:7,w7:8 (8 entries)
  floor        w0:1,w1:2,w2:3,w3:4,w4:5 (5 entries)
  compacted    w5:6,w6:7,w7:8 (3 entries)
  the five writers at the floor are past on every replica, so their counters distinguish nothing and 5 entries go
  -> holds
```

Story 5 is the one worth reading twice. Above the floor, compaction changed no verdict
in 6 comparisons. Below the floor, 6 of 15 comparisons changed, and all six changed the
same way: two different states collapsed into the same compacted vector, which reads as
`equal`. That is not a bug in `compact` - it is what discarding information does.

## Using it

```
$ {{ npm_name }} merge --left a:2 --right b:3
left         a:2
right        b:3
relation     concurrent
merged       a:2,b:3
dominance    the merge is after both: True

$ {{ npm_name }} prune --vector a:3,b:5,c:2 --floor a:2,b:5,c:1
vector       a:3,b:5,c:2 (3 entries)
floor        a:2,b:5,c:1
compacted    a:3,c:2 (2 entries)
dropped      1
sound        yes: this vector is above the floor, so the verdict survives

$ {{ npm_name }} pairs --vectors fixtures/vectors.jsonl
vector        a-only        b-only        both-a-first  both-b-first  all-three
a-only        -             X             <             X             <
b-only        X             -             X             <             <
both-a-first  >             X             -             X             <
both-b-first  X             >             X             -             <
all-three     >             >             >             >             -
legend        < before, > after, = equal, X concurrent
concurrent    4 pair(s) out of 10
```

`pairs` takes a JSONL file of `{"name": ..., "vector": ...}` rows and prints the whole
relation matrix, because a matrix is the honest picture of a partial order: some cells
are unordered and no amount of sorting removes them.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the answer is ordered (or the file has no concurrency) |
| 1 | the answer is `concurrent`, or the vector is below the floor |
| 2 | the input could not be read: bad vector text, missing file, unknown command |

Exit code 1 is a data answer, not a failure: a script that wants to stop on concurrency
asks for exactly that by checking the code.

## Layout

```
src/{{ package_name }}/vector.py    the counters, the comparison, merge, explain
src/{{ package_name }}/lamport.py   the total order, and the unrelated local work it cannot see
src/{{ package_name }}/causal.py    replicas, messages, the delivery gate
src/{{ package_name }}/prune.py     the floor, compaction, and the measurement
src/{{ package_name }}/demo.py      six stories, each one with a claim to check
src/{{ package_name }}/cli.py       compare, merge, prune, pairs, demo, selftest
```

## What this package does not do

- It does not pick a winner for concurrent writes. That is a merge policy (last write,
  union, application-specific), and choosing one silently is how lost updates happen.
- It does not implement a wire format. `text()` and `as_dict()` are enough to ship a
  vector in JSON, but the protocol around it - retries, ids, auth - is yours.
- It does not measure clock skew. A vector says nothing about time; that is the point.
- It does not check that a remote vector is honest. A replica that claims counters it
  never incremented is indistinguishable from one that did the work.

# {{ title }}

{{ description }}

Keys are placed by hashing them into a 64-bit ring and walking clockwise to the next node
point. That is the whole trick, and it has consequences that are easy to state and easy to
get wrong. This stack measures every one of them.

## The rules this ring keeps

1. **One hash, stable across restarts.** Keys are hashed with `blake2b(digest_size=8)`, not
   with Python's `hash()`: the builtin is salted per interpreter, so a restarted process
   would put every key on a different node and call it "rebalancing".
2. **A node is many points, not one.** `vnodes` points per unit of weight is what makes the
   share of keys close to the share of weight. One point per node is a lottery: see the
   arc-imbalance column in the demo.
3. **A weight is a number of points.** `add("big", weight=3)` puts three times the points on
   the ring, and the share of keys converges on three times the share of `small`.
4. **The ring wraps.** A key hashing past the last point belongs to the first one. A lookup
   that runs off the end and returns nothing is a dropped key, not an empty one.
5. **Insertion order is irrelevant.** The ring is sorted by where the points land, so the
   mapping does not depend on when nodes joined or in what order you list them.
6. **Removing a node moves only its own keys.** This is the property modulo hashing lacks:
   with `hash % N` every slot changes when N changes, so adding one node relocates strangers.
7. **A topology change is a checked operation.** `move` refuses to call a result good unless
   every moved key moved *onto a new node*, and the count stays inside a limit — by default
   1.5x the arriving nodes' fair share.

## What the demo prints

Real output of `{{ npm_name }} demo`, not an illustration:

```
1. adding a node: modulo remaps almost everything, a ring does not
  keys            5000
  modulo          4182 moved (83.6%)
  ring            907 moved (18.1%)
  the new node's fair share is one sixth, 16.7%
  modulo has no idea what it moved: every slot changes
```

```
3. virtual nodes are what make the split even
  vnodes   arc imbalance   measured   min/max keys
       1          271.64     309.64      11/3406
       4            2.55       3.00     530/1589
      20            1.73       1.70     790/1342
     160            1.23       1.05     971/1016
     640            1.08       1.18     917/1081
  one point per node is not a ring, it is a lottery
  arc imbalance is the ring's own shape; the measured column samples 5,000 keys
  and stops improving once the sample, not the ring, is the limit
```

The two columns are the point: `arc imbalance` comes from the point spacing alone and falls
monotonically as points are added; `measured` samples 5,000 keys and stops improving, because
past ~160 points the *sample* is the limit, not the ring. A single "imbalance" number without
saying how it was measured is how rings get argued about instead of tested.

## Commands

```
{{ npm_name }} map     --nodes alpha,bravo,charlie --keys 5000 [--vnodes 160] [--json]
{{ npm_name }} ring    --nodes alpha,bravo,charlie --key user:00001 [--weights delta=3]
{{ npm_name }} move    --nodes alpha,bravo,charlie --add delta --keys 5000 [--max-moved 25] [--show 5]
{{ npm_name }} balance --nodes alpha,bravo,charlie --keys 5000 [--max-imbalance 1.5]
{{ npm_name }} demo
{{ npm_name }} selftest
```

`move` on the 5-to-6 node case:

```
nodes        5 -> 6
added        foxtrot
moved        898 of 5000 (18.0%)
fair share   16.7%
limit        25.0%
modulo       82.7% would have moved
strangers    0 (keys that moved to a node that was already there)
gate         ok (18.0% <= 25.0%)
```

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the answer, or the gate passed |
| 1 | a gate failed: too many keys moved, a stranger moved, or the split is too uneven |
| 2 | the request does not describe a ring we can build (bad node list, bad weight, zero keys) |

`map`, `ring` and `demo` exit 0. `move` exits 1 when more than the limit moved or when a key
landed on a node that was already on the ring. `balance` exits 1 when the measured imbalance
is above `--max-imbalance`. An empty ring refuses lookups rather than returning a default.

## Layout

```
src/{{ package_name }}/hashing.py   blake2b hash, virtual node keys, mod_slot baseline
src/{{ package_name }}/ring.py      Point, Ring, arc loads, loads, shares, imbalance
src/{{ package_name }}/audit.py     who moved, and whether it had any business moving
src/{{ package_name }}/demo.py      the six stories above, computed every run
src/{{ package_name }}/cli.py       map, ring, move, balance, demo, selftest
src/{{ package_name }}/selftest.py  the same promises checked without pytest
tests/                              pytest versions of those checks
smoke.sh                            real CLI runs, including the failing gates
```

## What this stack does not do

- No replication or failover: one key, one owner. A second copy is a second ring with a
  different salt, and pretending otherwise hides the failure you meant to test.
- No gossip or membership protocol: the ring here is a data structure, not a cluster.
- No persistence: a ring is cheap to rebuild from the node list, and a stale saved ring is
  the thing that makes "the mapping changed for no reason" bugs.

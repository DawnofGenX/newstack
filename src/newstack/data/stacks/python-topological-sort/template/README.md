# {{ title }}

{{ description }}

order(graph) answers a predecessors-first listing of a small
integer-keyed digraph — every node exactly once, the same sequence
the naive picker answers — and cycle(graph) names the block honestly
when a cycle blocks the listing. A node is released only when its
last predecessor has gone; a tangled graph is refused, never shuffled.

## Why

A listing earns the name order the only way a listing can: it must
validate against every shipped edge, seat every node once, and answer
the same sequence in every run — and a fast answer that drifts from
the dumb answer is worthless. So this tool exists to *show* that, not
to state it:

```sh
$ {{ npm_name }} order 1 2 3 4 "1>2" "1>4" "2>3" "4>3"
```

Every claim below is a comparison the selftest computes at run
time against the real modules, and `selftest` refuses to pass when
one stops holding. The falsifiable core is the equality: `oracle.py`
answers every order by repeatedly picking the least node whose
predecessors have all gone, and every sequence `order()` hands back
must be that sequence, seat for seat.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the order answers the picker | a fast answer that drifts | order equals naive_order on shipped and seeded corpora |
| every listing validates | an edge pointing backward | the shipped validator walks every pair of every listing |
| every node is seated once | a dropped or invented node | the listing's count is the graph's count, islands included |
| the order is a fixed point | a sequence that wobbles | re-running the same graph answers the same sequence |
| a tangle names its block | a shuffled list over a cycle | cycle() names it, block() holds it, order() refuses |
| loud labels are refused | floats, words, half pairs | the door names the token, no graph is built |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} order 1 2 3 4 "1>2" "1>4" "2>3" "4>3"
uv run {{ npm_name }} check "1>2>4>3" 1 2 3 4 "1>2" "1>4" "2>3" "4>3"
uv run {{ npm_name }} report --corpus fixtures/graphs.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `order GRAPH` | the predecessors-first listing, or the refusal |
| `check LISTING GRAPH` | whether a listing seats every node, every edge forward |
| `cycles GRAPH` | the block, named — or clear |
| `report --corpus FILE` | a corpus walked, graph after graph |
| `demo` | six stories about orders, with real numbers |
| `selftest` | the promises, runnable in a fresh checkout |

## Input format

Nodes are integer labels from 0 to 999; a graph holds at most 64
nodes. A graph is spaced tokens: bare labels declare nodes, `A>B`
declares a directed pair (and admits both ends), so `1 2 1>2` is two
nodes and one pair. `fixtures/graphs.txt` is one graph per line;
blank lines and lines starting with `#` are skipped, and every other
line must pass the door. The JSON face of a listing is an object of
sequence: `{"order": [1, 2, 3]}`.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the promises hold |
| 1 | the order drifted from the picker, a listing broke, a story fails |
| 2 | the input cannot be read: a loud label, a tangle, a bad file |

## Files

```
src/{{ package_name }}/order.py          the order: order, validate, block
src/{{ package_name }}/oracle.py         the picker: the order, answered slow
src/{{ package_name }}/cycle.py          the tangle named: cycle, deterministic
src/{{ package_name }}/graph.py          the door: labels, pairs, the token face
src/{{ package_name }}/corpus.py         graphs in, reports out
src/{{ package_name }}/demo.py           six stories, every claim computed
src/{{ package_name }}/cli.py            the command line
src/{{ package_name }}/selftest.py       the promises, runnable in a checkout
fixtures/graphs.txt                      a corpus the smoke test builds on
smoke.sh                                 the tool driven the way a user drives it
```

## Non-goals

No labels past 999, no graphs past 64 nodes, no weighted edges, no
multigraphs, no general graph library, no persisted storage, no
all-hammock enumeration. The orderer is the honest Kahn it is: a
tool for showing what a sorted frontier owes a picker, not a
replacement for `networkx`.

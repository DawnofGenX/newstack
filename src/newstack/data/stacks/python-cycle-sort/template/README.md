# {{ title }}

{{ description }}

spanning_tree(graph) answers the edge set of a minimum spanning
tree over a small nonneg-weight undirected integer-keyed graph —
and the set's total equals the enumeration oracle's minimum, graph
after graph: the sorted walk joins fragments and refuses cycles.
tree_cost(graph) answers the total, witness(graph) the honest
per-edge ledger. Edges are owned once and answered once, lowest
pair first, so the face never doubles an edge.

## Why

A spanning tree earns trust the only way a tree can: its total
must be the enumeration's minimum, on every graph — and a cheap
answer that drifts from the dumb answer is worthless. So this tool
exists to *show* that, not to state it:

```sh
$ {{ npm_name }} tree 1 2 3 "1>2=4" "2>3=1" "1>3=1"
```

Every claim below is a comparison the selftest computes at run
time against the real modules, and `selftest` refuses to pass when
one stops holding. The falsifiable core is the equality:
`oracle.py` answers the minimum by enumerating every spanning tree
by subset (small n, dumb, complete) and taking the least, and the
total of every tree the walker hands back must be that minimum
exactly. `witness.py`'s ledger is the walk's own confession — the
promise that cycles are refused, the product is the walk of the
sorted list.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the walker answers the enumeration | a cheap answer that drifts | tree_cost equals min_cost on shipped and seeded corpora |
| the tree is a tree | an edge set that lies about its shape | \|V\|-1 edges, every node touched, one piece |
| the ledger tells the truth | a taken edge that closed a cycle | witness taken-edges equal the tree, per graph |
| the walk is sorted once | a walk that shuffles its list | ledger weights read nondecreasing |
| ties stay still | a tree that changes between runs | equal weights pick the same edge set, run after run |
| a graph in pieces is named | an invented half-tree | disconnected input raises, no partial answer ships |
| a weight is spoken, never assumed | a silent default weight | A>B without A>B=W is refused at the door |
| loud labels are refused | floats, loops, oversized labels | the door names the token, no graph is built |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} tree 1 2 3 "1>2=4" "2>3=1" "1>3=1"
uv run {{ npm_name }} witness 1 2 3 "1>2=4" "2>3=1" "1>3=1"
uv run {{ npm_name }} report --corpus fixtures/graphs.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `tree GRAPH` | the edge set the walker and the enumeration agree on |
| `witness GRAPH` | the walk's per-edge ledger, taken-or-skipped, reasoned |
| `report --corpus FILE` | a corpus walked, graph after graph |
| `demo` | six stories about walks, with real numbers |
| `selftest` | the promises, runnable in a fresh checkout |

## Input format

Nodes are integer labels from 0 to 999; weights are nonneg integers
to the same ceiling; a graph holds at most 32 nodes. A graph is
spaced tokens: bare labels declare nodes, `A>B=W` declares a
weighted edge (and admits both ends), so `1 2 1>2=4` is two nodes
and one costed edge. The graph is undirected: every edge is owned
once, keyed by its lowest-first pair, and `edges()` answers each
edge once as that pair. `A>B` without a weight is refused — a
silent default is how wrong trees get shipped. `A>A` is a loop and
is refused. `fixtures/graphs.txt` is one connected graph per line;
blank lines and lines starting with `#` are skipped, and every
other line must pass the door. The JSON face of a tree is a list
of `{"edge": [low, high], "weight": w}` objects, lowest pair first;
the JSON face of a ledger adds `"taken"` and `"reason"`.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the promises hold |
| 1 | the walker drifted from the enumeration, a story fails |
| 2 | the input cannot be read: a loud label, a mute edge, a bad file |

## Files

```
src/{{ package_name }}/solve.py          the walker: spanning_tree, tree_cost, witness
src/{{ package_name }}/oracle.py         the enumeration: the minimum, answered slow
src/{{ package_name }}/graph.py          the door: labels, weights, the token face
src/{{ package_name }}/corpus.py         connected graphs in, reports out
src/{{ package_name }}/demo.py           six stories, every claim computed
src/{{ package_name }}/cli.py            the command line
src/{{ package_name }}/selftest.py       the promises, runnable in a checkout
fixtures/graphs.txt                      a corpus the smoke test builds on
smoke.sh                                 the tool driven the way a user drives it
```

## Non-goals

No labels past 999, no negative weights, no graphs past 32 nodes,
no multigraphs, no loops, no float weights, no general graph
library, no persisted storage, no directed graphs, no incremental
updates. The walker is the honest Cycle it is: a tool for
showing what one sorted list owes a complete enumeration, not a
replacement for `networkx`.

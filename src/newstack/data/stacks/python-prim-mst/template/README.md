# {{ title }}

{{ description }}

spanning_tree(graph, start) answers the edge set of a minimum
spanning tree over a small nonneg-weight undirected integer-keyed
graph — and the set's total equals the enumeration oracle's
minimum, graph after graph: a node joins the tree once, through
the cheapest crossing edge. tree_cost(graph, start) answers the
total. Edges are held in both adjacency directions and answered
once, lowest pair first, so the face never doubles an edge.

## Why

A spanning tree earns trust the only way a tree can: its total
must be the enumeration's minimum, on every graph — and a cheap
answer that drifts from the dumb answer is worthless. So this tool
exists to *show* that, not to state it:

```sh
$ {{ npm_name }} cost 1 1 2 3 "1>2=4" "2>3=1" "1>3=1"
```

Every claim below is a comparison the selftest computes at run
time against the real modules, and `selftest` refuses to pass when
one stops holding. The falsifiable core is the equality:
`oracle.py` answers the minimum by enumerating every spanning tree
by subset (small n, dumb, complete) and taking the least, and the
total of every tree the grower hands back must be that minimum
exactly.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the grower answers the enumeration | a cheap answer that drifts | tree_cost equals min_cost on shipped and seeded corpora |
| the tree is a tree | an edge set that lies about its shape | \|V\|-1 edges, every node touched, one piece |
| ties stay still | a tree that changes between runs | equal weights pick the same edge set, run after run |
| a graph in pieces is named | an invented half-tree | disconnected input raises, no partial answer ships |
| a weight is spoken, never assumed | a silent default weight | A>B without A>B=W is refused at the door |
| loud labels are refused | floats, loops, oversized labels | the door names the token, no graph is built |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} tree 1 1 2 3 "1>2=4" "2>3=1" "1>3=1"
uv run {{ npm_name }} cost 1 1 2 3 "1>2=4" "2>3=1" "1>3=1"
uv run {{ npm_name }} report --corpus fixtures/graphs.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `tree START GRAPH` | the edge set the grower and the enumeration agree on |
| `cost START GRAPH` | the total the edge set carries |
| `report --corpus FILE` | a corpus grown, graph after graph |
| `demo` | six stories about trees, with real numbers |
| `selftest` | the promises, runnable in a fresh checkout |

## Input format

Nodes are integer labels from 0 to 999; weights are nonneg integers
to the same ceiling; a graph holds at most 32 nodes. A graph is
spaced tokens: bare labels declare nodes, `A>B=W` declares a
weighted edge (and admits both ends), so `1 2 1>2=4` is two nodes
and one costed edge. The graph is undirected: every edge is held
in both adjacency directions, and `edges()` answers each edge once
as a lowest-first pair. `A>B` without a weight is refused — a
silent default is how wrong trees get shipped. `A>A` is a loop and
is refused. `fixtures/graphs.txt` is one connected graph per line;
blank lines and lines starting with `#` are skipped, and every
other line must pass the door. The JSON face of a tree is a list
of `{"edge": [low, high], "weight": w}` objects, lowest pair first.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the promises hold |
| 1 | the grower drifted from the enumeration, a story fails |
| 2 | the input cannot be read: a loud label, a mute edge, a bad file |

## Files

```
src/{{ package_name }}/solve.py          the grower: spanning_tree, tree_cost, audit
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
updates. The grower is the honest Prim it is: a tool for showing
what one frontier owes a complete enumeration, not a replacement
for `networkx`.

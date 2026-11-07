# {{ title }}

{{ description }}

distances(graph) answers the all-pairs distance table over a small
nonneg-weight integer-keyed digraph — and the table equals the
walking oracle's table, pair for pair: the matrix seeds every node
at zero, sits every arrow at its weight, and lets every node speak
as a stepping stone until nothing moves. worst_hop(graph) answers
the most distant reachable pair. An arrow points one way: a pair
the arrows never carry is omitted, never spoken as infinity.

## Why

A distance table earns trust the only way a table can: it must be
the walker's own answer, on every graph — and a fast table that
drifts from the dumb walk is worthless. So this tool exists to
*show* that, not to state it:

```sh
$ {{ npm_name }} table 1 2 3 "1>2=4" "2>3=1" "1>3=9"
```

Every claim below is a comparison the selftest computes at run
time against the real modules, and `selftest` refuses to pass when
one stops holding. The falsifiable core is the equality:
`oracle.py` answers the table one source at a time — relax every
out-arrow, repeat to a fixed point, no matrix loop — and the
matrix's table must equal that table exactly, cell for cell, on
every graph the corpora hold.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the table answers the walker | a fast answer that drifts | distances equals distance_table on shipped and seeded corpora |
| the diagonal stands still | a node that owes itself a fare | every node sits at zero on itself |
| the table rests | a table that moves under one more sweep | restated(table) equals table, the triangle inequality kept |
| an arrow points | an invented back road | an unreached ordered pair is omitted, never infinity |
| a weight is spoken, never assumed | a silent default weight | A>B without A>B=W is refused at the door |
| loud labels are refused | floats, loops, oversized labels | the door names the token, no graph is built |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} table 1 2 3 "1>2=4" "2>3=1" "1>3=9"
uv run {{ npm_name }} worst 1 2 3 "1>2=4" "2>3=1" "1>3=9"
uv run {{ npm_name }} report --corpus fixtures/graphs.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `table GRAPH` | the all-pairs distance table the walker and the matrix agree on |
| `worst GRAPH` | the most distant reachable pair and its cost |
| `report --corpus FILE` | a corpus walked, graph after graph |
| `demo` | six stories about tables, with real numbers |
| `selftest` | the promises, runnable in a fresh checkout |

## Input format

Nodes are integer labels from 0 to 999; weights are nonneg integers
to the same ceiling; a graph holds at most 32 nodes. A graph is
spaced tokens: bare labels declare nodes, `A>B=W` declares a
weighted arrow from A to B (and admits both ends), so `1 2 1>2=4`
is two nodes and one costed arrow. The graph is a digraph: `A>B`
points one way and `B` is no way back, so `edges()` answers ordered
pairs. `A>B` without a weight is refused — a silent default is how
wrong tables get shipped. `A>A` is a loop and is refused.
`fixtures/graphs.txt` is one digraph per line; blank lines and lines
starting with `#` are skipped, and every other line must pass the
door. The JSON face of a table is a list of `{"pair": [source,
target], "cost": c}` objects, lowest pair first; unreached ordered
pairs simply do not appear.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the promises hold |
| 1 | the table drifted from the walk, a story fails |
| 2 | the input cannot be read: a loud label, a mute arrow, a bad file |

## Files

```
src/{{ package_name }}/solve.py          the matrix: distances, worst_hop, audit
src/{{ package_name }}/oracle.py         the walker: the table, answered slow
src/{{ package_name }}/graph.py          the door: labels, weights, the token face
src/{{ package_name }}/corpus.py         digraphs in, reports out
src/{{ package_name }}/demo.py           six stories, every claim computed
src/{{ package_name }}/cli.py            the command line
src/{{ package_name }}/selftest.py       the promises, runnable in a checkout
fixtures/graphs.txt                      a corpus the smoke test builds on
smoke.sh                                 the tool driven the way a user drives it
```

## Non-goals

No labels past 999, no negative weights, no graphs past 32 nodes,
no multigraphs, no loops, no float weights, no general graph
library, no persisted storage, no undirected shortcuts, no
incremental updates. The matrix is the honest Floyd-Warshall it
is: a tool for showing what one stepping-stone loop owes one fixed
point, not a replacement for `networkx`.

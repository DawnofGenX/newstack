# {{ title }}

{{ description }}

distances(graph, source) answers the cheapest cost to every
reached node of a small weighted integer-keyed digraph — and the
map is the relaxation oracle's map, key for key: a node is settled
only when no edge can lower its cost. path(graph, source, target)
answers the cheapest route, and the route costs exactly what the
map says. Unreachable nodes are omitted: omission is this
library's spelling of unreachable, on every face it answers.

## Why

A shortest-path walker earns trust the only way a walker can: its
map must be the fixed point's map, on every graph — and a fast
answer that drifts from the dumb answer is worthless. So this tool
exists to *show* that, not to state it:

```sh
$ {{ npm_name }} distances 1 1 2 3 "1>2=4" "2>3=3" "1>3=9"
```

Every claim below is a comparison the selftest computes at run
time against the real modules, and `selftest` refuses to pass when
one stops holding. The falsifiable core is the equality:
`oracle.py` answers every distance map by relaxing the whole edge
list to a fixed point, and every map the walker hands back must be
that map exactly.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the walker answers the fixed point | a fast answer that drifts | distances equals relax_map on shipped and seeded corpora |
| every route costs the map | a route that lies about its cost | every shipped path's cost is the map's cost for its target |
| unreachable stays honest | an invented cost | an unreached node keys nothing, on every map, every face |
| no edge still lowers a keyed node | a map that missed a door | the audit walks every edge of every map |
| a weight is spoken, never assumed | a silent default weight | A>B without A>B=W is refused at the door |
| loud labels are refused | floats, words, negatives, oversized labels | the door names the token, no graph is built |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} distances 1 1 2 3 "1>2=4" "2>3=3" "1>3=9"
uv run {{ npm_name }} path 1 3 1 2 3 "1>2=4" "2>3=3" "1>3=9"
uv run {{ npm_name }} report --corpus fixtures/graphs.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `distances SOURCE GRAPH` | the map the walker and the fixed point agree on |
| `path SOURCE TARGET GRAPH` | the cheapest route and its cost |
| `report --corpus FILE` | a corpus walked, graph after graph |
| `demo` | six stories about routes, with real numbers |
| `selftest` | the promises, runnable in a fresh checkout |

## Input format

Nodes are integer labels from 0 to 999; weights are nonneg integers
to the same ceiling; a graph holds at most 64 nodes. A graph is
spaced tokens: bare labels declare nodes, `A>B=W` declares a
weighted edge (and admits both ends), so `1 2 1>2=4` is two nodes
and one costed edge. `A>B` without a weight is refused — a silent
default is how wrong routes get shipped. `fixtures/graphs.txt` is
one graph per line; blank lines and lines starting with `#` are
skipped, and every other line must pass the door. The JSON face of
a map is an object of label to cost: `{"1": 0, "2": 4, "3": 7}`.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the promises hold |
| 1 | the walker drifted from the fixed point, a story fails |
| 2 | the input cannot be read: a loud label, a mute edge, a bad file |

## Files

```
src/{{ package_name }}/solve.py          the walker: distances, path, audit
src/{{ package_name }}/oracle.py         the fixed point: the map, answered slow
src/{{ package_name }}/graph.py          the door: labels, weights, the token face
src/{{ package_name }}/corpus.py         weighted graphs in, reports out
src/{{ package_name }}/demo.py           six stories, every claim computed
src/{{ package_name }}/cli.py            the command line
src/{{ package_name }}/selftest.py       the promises, runnable in a checkout
fixtures/graphs.txt                      a corpus the smoke test builds on
smoke.sh                                 the tool driven the way a user drives it
```

## Non-goals

No labels past 999, no negative weights, no graphs past 64 nodes,
no multigraphs, no float weights, no general graph library, no
persisted storage, no all-pairs beyond repeated single sources.
The walker is the honest Dijkstra it is: a tool for showing what
one frontier owes a fixed point, not a replacement for `networkx`.

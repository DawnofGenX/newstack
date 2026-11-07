# {{ title }}

{{ description }}

partition(graph) answers the strongly-connected components of a
small integer-keyed digraph in one walk — and the answer is the
reachability oracle's partition, component for component: two
nodes share a component only when each reaches the other.
condense(graph) folds every component to its smallest label and
answers the DAG the crossings trace. The promise is checked,
never assumed: the walker equals the shipped O(n^2) closure on
every shipped and seeded corpus, and the condensed graph clears
the shipped cycle checker.

## Why

A component walker earns trust the only way a walker can: its
partition must be the closure's partition, on every graph — and a
fast answer that drifts from the dumb answer is worthless. So
this tool exists to *show* that, not to state it:

```sh
$ {{ npm_name }} components 1 2 3 "1>2" "2>3" "3>1" "3>4"
```

Every claim below is a comparison the selftest computes at run
time against the real modules, and `selftest` refuses to pass when
one stops holding. The falsifiable core is the equality: `oracle.py`
answers every partition by crawling the transitive closure, and
every partition the walker hands back must be that partition
exactly.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the walker answers the oracle | a fast answer that drifts | partition equals oracle_partition on shipped and seeded corpora |
| every node has one seat | a node lost or double-counted | the seats are the nodes, once, on every graph |
| the fold is acyclic | two components in a ring | has_cycle walks every condensed graph and finds none |
| the fold keeps the crossings | an edge dissolved by luck | between-component edges survive, inside ones vanish |
| a ring walks whole | a splitter where there is none | one component, the closure agrees |
| a chain walks apart | a merger where there is none | one component per node, the closure agrees |
| loud labels are refused | floats, words, oversized labels | the door names the label, no graph is built |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} components 1 2 3 "1>2" "2>3" "3>1" "3>4"
uv run {{ npm_name }} condense 0 1 2 "0>1" "1>2"
uv run {{ npm_name }} report --corpus fixtures/graphs.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `components GRAPH` | the partition the walker and the oracle agree on |
| `condense GRAPH` | the DAG the components fold to |
| `report --corpus FILE` | a corpus walked, graph after graph |
| `demo` | six stories about components, with real numbers |
| `selftest` | the promises, runnable in a fresh checkout |

## Input format

Nodes are integer labels from 0 to 999; a graph holds at most 64
of them. A graph is spaced tokens: bare labels declare nodes,
`A>B` declares an edge (and admits both ends), so `1 2 1>2` is two
nodes and one edge. `fixtures/graphs.txt` is one graph per line;
blank lines and lines starting with `#` are skipped, and every
other line must pass the door. The JSON face of a partition is a
list of sorted lists: `[[1, 2, 3], [4]]`.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the promises hold |
| 1 | the walker drifted from the oracle, a story fails |
| 2 | the input cannot be read: a loud label, a bad file |

## Files

```
src/{{ package_name }}/scc.py           the walker: partition, condense, audit
src/{{ package_name }}/oracle.py        the closure: the partition, answered slow
src/{{ package_name }}/graph.py         the door: labels, edges, the token face
src/{{ package_name }}/cycle.py         the checker the condensed graph clears
src/{{ package_name }}/corpus.py        graphs in, reports out
src/{{ package_name }}/demo.py          six stories, every claim computed
src/{{ package_name }}/cli.py           the command line
src/{{ package_name }}/selftest.py      the promises, runnable in a checkout
fixtures/graphs.txt                     a corpus the smoke test builds on
smoke.sh                                the tool driven the way a user drives it
```

## Non-goals

No labels past 999, no graphs past 64 nodes, no multigraphs, no
edge weights, no general graph library, no persisted storage, no
topological sorting beyond the fold. The walker is the honest
Tarjan it is: a tool for showing what one pass owes a closure, not
a replacement for `networkx`.

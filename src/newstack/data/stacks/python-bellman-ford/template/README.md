# {{ title }}

{{ description }}

distances(graph, source) answers the shortest-path map of a small
integer-weighted digraph in |V|-1 relaxation rounds - and the answer
is the walk-counting oracle's map, node for node: no cheaper walk
survives a settled edge. negative_cycle(graph, source) names the
cycle honestly when one keeps pulling a walk down. The promise is
checked, never assumed: the walker equals the shipped walk-counting
oracle on every shipped and seeded corpus, and after |V|-1 rounds no
shipped edge still relaxes.

## Why

A weight walker earns trust the only way a walker can: its distance
map must be the count's map, on every graph - and a fast answer that
drifts from the dumb answer is worthless. So this tool exists to
*show* that, not to state it:

```sh
$ {{ npm_name }} distances 1 2 3 4 "1>2=4" "2>3=-2" "3>4=3" "1>3=5" "2>4=1" --source 1
```

Every claim below is a comparison the selftest computes at run time
against the real modules, and `selftest` refuses to pass when one
stops holding. The falsifiable core is the equality: `oracle.py`
answers every map by enumerating walks up to |V|-1 edges, and every
map the walker hands back must be that map exactly.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the walker answers the oracle | a fast answer that drifts | distances equals oracle_distances on shipped and seeded corpora |
| no edge survives settled | a map the rounds missed | the shipped checker names every relaxing edge and finds none |
| a negative weight walks | a direct edge taken on faith | the cheap route through -2 wins, the count agrees |
| a cycle is named, not walked past | a distance no walk finishes with | negative_cycle names (0, 1, 2) on the shipped fixture |
| unreachable answers honestly | a cost invented from nowhere | UNREACHED, never a made-up number |
| loud labels are refused | floats, words, unweighted edges | the door names the token, no graph is built |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} distances 1 2 3 4 "1>2=4" "2>3=-2" "3>4=3" "1>3=5" "2>4=1" --source 1
uv run {{ npm_name }} cycles 0 1 2 "0>1=-2" "1>2=1" "2>0=0" --source 0
uv run {{ npm_name }} report --corpus fixtures/graphs.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `distances GRAPH --source N` | the map the walker and the count agree on |
| `cycles GRAPH --source N` | the negative cycle, named or honestly none |
| `report --corpus FILE` | a corpus walked, graph after graph |
| `demo` | six stories about weighted walks, with real numbers |
| `selftest` | the promises, runnable in a fresh checkout |

## Input format

Nodes are integer labels from 0 to 999; weights are integers from
-999 to 999; a graph holds at most 64 nodes. A graph is spaced
tokens: bare labels declare nodes, `A>B=W` declares a weighted edge
(and admits both ends), so `1 2 1>2=-4` is two nodes and one edge.
An unweighted `A>B` is refused - weights are the subject here.
`fixtures/graphs.txt` is one graph per line; blank lines and lines
starting with `#` are skipped, and every other line must pass the
door. The JSON face of a map is an object: `{"1": 0, "2": -5}`.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the promises hold |
| 1 | the walker drifted from the oracle, a story fails |
| 2 | the input cannot be read: a loud label, a bad file |

## Files

```
src/{{ package_name }}/walk.py          the walker: distances, settled, audit
src/{{ package_name }}/oracle.py        the count: the map, answered slow
src/{{ package_name }}/graph.py         the door: labels, weights, the token face
src/{{ package_name }}/cycle.py         the answer a negative cycle forces
src/{{ package_name }}/corpus.py        graphs in, reports out
src/{{ package_name }}/demo.py          six stories, every claim computed
src/{{ package_name }}/cli.py           the command line
src/{{ package_name }}/selftest.py      the promises, runnable in a checkout
fixtures/graphs.txt                     a corpus the smoke test builds on
smoke.sh                                the tool driven the way a user drives it
```

## Non-goals

No labels past 999, no weights past 999, no graphs past 64 nodes, no
floats, no multigraphs, no general graph library, no persisted
storage, no all-pairs matrix. The walker is the honest Bellman-Ford
it is: a tool for showing what |V|-1 rounds owe a walk count, not a
replacement for `networkx`.

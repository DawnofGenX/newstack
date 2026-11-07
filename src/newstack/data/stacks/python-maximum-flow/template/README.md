# {{ title }}

{{ description }}

max_flow(graph, source, sink) answers the value a small
nonneg-integer-capacity integer-keyed digraph carries from a
designated source to a designated sink — and that value equals the
brute-force cut oracle's least, network after network: flow walks
the residual, never past a bottleneck. flow_map(graph, source,
sink) answers the shipped amount per arc, conserved at every
interior node.

## Why

Carried flow earns trust the only way flow can: its value must be
the enumeration's least cut, on every network — and a carried
answer that drifts from the dumb answer is worthless. So this tool
exists to *show* that, not to state it:

```sh
$ {{ npm_name }} flow 0 3 "0>1=3" "1>3=2" "0>2=2" "2>3=3" "0>3=1" "1>2=1"
```

Every claim below is a comparison the selftest computes at run
time against the real modules, and `selftest` refuses to pass when
one stops holding. The falsifiable core is the equality:
`oracle.py` answers the least cut by enumerating every subset
separating source from sink (small n, dumb, complete) and taking
the least, and the value the walker hands back must be that least
exactly.

## The rules

| rule | what it forbids | where it is proved |
| ---- | --------------- | ------------------ |
| the walker answers the enumeration | a carried answer that drifts | max_flow equals min_cut on shipped and seeded corpora |
| the map conserves inside | a leak at an interior node | in equals out at every non-end, audited per corpus |
| shipments respect capacities | a shipped amount past a door | every amount sits between zero and its arc's capacity |
| walks stay still | a flow that changes between runs | the same network ships the same map, run after run |
| a pair holds one channel | two-way channels and silent doubling | the opposite arc is refused; a repeat merges, documented |
| a capacity is spoken, never assumed | a silent default capacity | A>B without A>B=W is refused at the door |
| loud labels are refused | floats, loops, oversized labels | the door names the token, no network is built |

## Quick start

```sh
cd your-project
uv sync
uv run {{ npm_name }} flow 0 3 "0>1=3" "1>3=2" "0>2=2" "2>3=3" "0>3=1" "1>2=1"
uv run {{ npm_name }} map 0 3 "0>1=3" "1>3=2" "0>2=2" "2>3=3" "0>3=1" "1>2=1"
uv run {{ npm_name }} report --corpus fixtures/networks.txt
PY=.venv/bin/python bash smoke.sh
```

## Commands

| command | question it answers |
| ------- | ------------------- |
| `flow SOURCE SINK GRAPH` | the value the walker and the enumeration agree on |
| `map SOURCE SINK GRAPH` | the shipped amount per arc, audited before it ships |
| `report --corpus FILE` | a corpus walked, network after network |
| `demo` | six stories about carried flow, with real numbers |
| `selftest` | the promises, runnable in a fresh checkout |

## Input format

Nodes are integer labels from 0 to 999; capacities are nonneg
integers to the same ceiling; a network holds at most 32 nodes. A
network is spaced tokens: bare labels declare nodes, `A>B=W`
declares a directed capacityed arc (and admits both ends), so
`1 2 1>2=4` is two nodes and one arc. The graph is directed: `1>2`
and `2>1` are different arcs, and every arc is stored under its
own direction only. One pair of nodes holds one channel — a
repeated `A>B=W` merges its capacity into the channel already
standing, and `A>B` alongside a standing `B>A` is refused at the
door. `A>B` without a capacity speaks no room and is refused — a
silent default is how wrong shipments ship. `A>A` is a loop and is
refused. The source and sink are designated per question, never
stored. `fixtures/networks.txt` is one network per line; blank
lines and lines starting with `#` are skipped, arcs run upward
only, and the lowest label is the source and the highest the sink.
The JSON face of a map is a list of `{"arc": [source, target],
"shipped": amount}` objects, lowest arc first.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | an answer was given, or the promises hold |
| 1 | the walker drifted from the enumeration, a story fails |
| 2 | the input cannot be read: a loud label, a mute arc, a bad file |

## Files

```
src/{{ package_name }}/solve.py          the walker: max_flow, flow_map, audit
src/{{ package_name }}/oracle.py         the enumeration: the least cut, answered slow
src/{{ package_name }}/graph.py          the door: labels, capacities, the token face
src/{{ package_name }}/corpus.py         networks in, reports out
src/{{ package_name }}/demo.py           six stories, every claim computed
src/{{ package_name }}/cli.py            the command line
src/{{ package_name }}/selftest.py       the promises, runnable in a checkout
fixtures/networks.txt                    a corpus the smoke test builds on
smoke.sh                                 the tool driven the way a user drives it
```

## Non-goals

No labels past 999, no negative capacities, no networks past 32
nodes, no two-way channel between one pair, no loops, no float
capacities, no general graph library, no persisted storage, no
undirected networks, no stored source or sink. The walker is the
honest Edmonds-Karp it is: a tool for showing what one residual
owes a complete cut enumeration, not a replacement for `networkx`.

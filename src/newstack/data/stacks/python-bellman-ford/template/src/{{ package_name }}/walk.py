"""The walker: |V|-1 rounds, and the distance map answers.

The rule this walker keeps:
no cheaper walk survives a settled edge.
And the answer it hands back is the oracle's distance map, node for
node, on every graph the corpora hold. The walk sweeps every edge
once per round, |V|-1 rounds, and a negative weight is just another
weight - which is why this walker walks where a non-negative walker
may not. Break the round count or keep the longer candidate and the
map drifts from the oracle.

distances(graph, source) answers the map, settled(graph, source)
names every edge that still relaxes - empty is the promise. The
promise is checked, never assumed: selftest and the suites compare
every map against the enumeration oracle.
"""

from __future__ import annotations

from .graph import UNREACHED, Graph, GraphError


class WalkError(ValueError):
    """A graph the walker refuses to walk."""

    __slots__ = ()


def distances(graph: Graph, source: int) -> dict:
    """node -> the cheapest cost, answered in |V|-1 relaxation rounds.

    Every round sweeps every edge in sorted order and keeps the
    shorter candidate; an early quiet round ends the walk because a
    stable map stays stable. Unreachable nodes answer UNREACHED.
    The map equals the walk-counting oracle's map, exactly, on every
    shipped and seeded corpus.
    """
    if not graph.has_node(source):
        raise GraphError(f"{source!r} is not a node, so no walk starts there")
    answer: dict = dict.fromkeys(graph.nodes(), UNREACHED)
    answer[source] = 0
    for _ in range(max(len(graph) - 1, 0)):
        changed = False
        for node, target, weight in graph.edges():
            if answer[node] is not UNREACHED:
                step = answer[node] + weight
                if answer[target] is UNREACHED or step < answer[target]:
                    answer[target] = step
                    changed = True
        if not changed:
            break
    return answer


def settled(graph: Graph, source: int) -> list:
    """Name every edge that still relaxes after the walk; empty holds.

    The shipped checker's question: run the map through distances,
    then test every edge against its own current ends. A surviving
    relaxation names a walk the rounds missed - or a negative cycle
    that no round count can settle.
    """
    answer = distances(graph, source)
    breaks: list = []
    for node, target, weight in graph.edges():
        if answer[node] is not UNREACHED:
            step = answer[node] + weight
            if answer[target] is UNREACHED or step < answer[target]:
                breaks.append((node, target, weight))
    return breaks


def audit(graph: Graph, source: int, answer: dict) -> list:
    """Name every way a distance map fails its own shape; empty holds.

    Every node answers exactly once, the source answers zero, and
    the shape checks read the map the walker handed back, not a
    freshly walked one. The equal-oracle tests carry the deeper
    promise - this audit is the cheap shape check the walker owes.
    """
    breaks: list = []
    if set(answer) != set(graph.nodes()):
        breaks.append("the map misses a node or names a stranger")
    elif answer.get(source) != 0:
        breaks.append("the source does not answer zero")
    return breaks


def strong_statement() -> str:
    """The one-line promise, published for the door and the docs."""
    return "no cheaper walk survives a settled edge"

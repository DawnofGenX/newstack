"""The walker: the settled set, and the map that answers the oracle.

The rule this walker keeps, and the marker the detector looks for:
a node is settled only when no edge can lower its cost. The walk
carries a frontier of unsettled reached nodes; the frontier hands
up the cheapest entry, that entry is settled once, and its out-
edges offer their costs onward. Weights are nonneg, so a settled
cost is final - and the map it builds is the relaxation oracle's
map, key for key, on every graph the corpora hold.

distances(graph, source) answers the map, path(graph, source,
target) answers the cheapest route. Unreached nodes are omitted
from the map - omission is the spelling of unreachable everywhere
this library answers. The promise is checked, never assumed:
selftest and the suites compare every map against the oracle.
"""

from __future__ import annotations

from .graph import Graph

MAX_STEPS = 4096


class RouteError(ValueError):
    """A graph the walker refuses to walk, or a route it refuses to spin."""

    __slots__ = ()


def _frontier_min(frontier: dict) -> int:
    """The unsettled node carrying the cheapest offered cost.

    Cheapest means exactly that: labels are walked in order so ties
    settle low-label first, and the entry kept is the one with the
    lowest cost. Take the last unsettled entry instead and the
    walker stops being Dijkstra - it settles expensive nodes early
    and the map drifts from the fixed point.
    """
    chosen = None
    for node in sorted(frontier):
        if chosen is None or frontier[node] < frontier[chosen]:
            chosen = node
    return chosen


def _walk(graph: Graph, source: int) -> tuple:
    """The settled map and the parents the settlement walked in on."""
    if not graph.has_node(source):
        raise KeyError(f"{source!r} is not a node")
    costs: dict = {source: 0}
    parents: dict = {}
    frontier: dict = {source: 0}
    settled: set = set()
    steps = 0
    while frontier:
        steps += 1
        if steps > MAX_STEPS:
            raise RouteError("the walk spun past its step ceiling")
        node = _frontier_min(frontier)
        del frontier[node]
        if node in settled:
            continue
        settled.add(node)
        for target, weight in graph.successors(node):
            if target in settled:
                continue
            offered = costs[node] + weight
            if target not in costs or offered < costs[target]:
                costs[target] = offered
                parents[target] = node
                frontier[target] = offered
    return costs, parents


def distances(graph: Graph, source: int) -> dict:
    """node -> cheapest cost from source; unreachable nodes omitted.

    The settled frontier's answer, and the oracle's map exactly:
    every reached node carries its true cost, every unreached node
    carries no key. Compare the whole map, never a sample.
    """
    costs, _ = _walk(graph, source)
    return costs


def path(graph: Graph, source: int, target: int) -> tuple:
    """The cheapest route source -> target, as (nodes, cost).

    Walked from the same settlement as distances: the route's cost
    is the map's cost for the target, node for node the cheapest
    chain. A RouteError names a target the source never reaches -
    an honest miss beats an invented route.
    """
    if not graph.has_node(target):
        raise KeyError(f"{target!r} is not a node")
    costs, parents = _walk(graph, source)
    if target not in costs:
        raise RouteError(f"{target} is beyond the reach of {source}")
    if source == target:
        return (source,), 0
    route: list = [target]
    while route[-1] != source:
        route.append(parents[route[-1]])
    route.reverse()
    return tuple(route), costs[target]


def audit(graph: Graph, source: int, costs: dict) -> list:
    """Name every way a distance map fails its own shape; empty holds.

    Every key is a node, the source sits at zero, and no edge offers
    a cheaper door into a keyed node. The equal-oracle tests carry
    the deeper promise - this audit is the cheap shape check the
    walker owes its own answer.
    """
    breaks: list = []
    if source in costs and costs[source] != 0:
        breaks.append(f"{source} settled at {costs[source]}, not zero")
    for node in costs:
        if not graph.has_node(node):
            breaks.append(f"{node!r} keyed without a seat")
    for start, target, weight in graph.edges():
        if start in costs and target in costs:
            lowered = costs[start] + weight < costs[target]
            if lowered:
                breaks.append(f"{start}->{target} still lowers {target}")
    return breaks

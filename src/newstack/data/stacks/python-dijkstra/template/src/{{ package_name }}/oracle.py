"""The oracle: the dumb fixed point that never misses, only crawls slow.

The distance map this library sells is the one this oracle answers:
costs start at the source, every edge is relaxed over and over
until nothing moves. No priority queue, no settling order, no
cleverness - Bellman-Ford-style repeated relaxation over the whole
edge list until the map stops changing. The walker in solve.py must
agree with it, key for key, on every graph the corpora hold.

Unreachable nodes are omitted from the map: a node the source never
reaches has no cost to report, and a missing key beats an infinity
token a caller must remember to unwrap.

The oracle is the product. The walker is the way to afford it.
"""

from __future__ import annotations

from .graph import Graph


def relax_map(graph: Graph, source: int) -> dict:
    """node -> cheapest cost from source, answered by relaxation alone.

    Costs start at zero for the source and nothing else; the edge
    list is swept until a full sweep moves no cost. A node the
    sweeps never reach stays out of the map - omission is this
    library's spelling of unreachable, on every face it answers.
    """
    if not graph.has_node(source):
        raise KeyError(f"{source!r} is not a node")
    costs: dict = {source: 0}
    edges = graph.edges()
    moved = True
    while moved:
        moved = False
        for start, target, weight in edges:
            if start not in costs:
                continue
            offered = costs[start] + weight
            if target not in costs or offered < costs[target]:
                costs[target] = offered
                moved = True
    return costs


def oracle_distances(graph: Graph, source: int) -> dict:
    """The distance map, answered slow: the walker's published promise."""
    return relax_map(graph, source)

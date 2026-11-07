"""The oracle: the walker that never misses, only crawls slow.

No matrix loop, no ordering, no cleverness: one source at a time,
relax every out-arrow from scratch, repeat until the answers stop
moving - a fixed point. What the walker reaches, the table must
reach at the same cost; what the walker omits, the table must
omit. The walker is the product. The matrix is the way to afford it.

The graph is a digraph: every walk follows the arrows, and a pair
the arrows never carry is a pair no table speaks.
"""

from __future__ import annotations

from .graph import Graph

MAX_SWEEPS = 256


class OracleError(ValueError):
    """A graph the walker refuses to walk, or a shape it refuses."""

    __slots__ = ()


def walk_from(graph: Graph, source: int) -> dict:
    """Every node the source reaches, with its least cost; others omitted.

    The dumb walk: re-relax every out-arrow of every found node until
    an entire sweep moves nothing. No matrix, no ordering - small
    graphs, where a fixed point is affordable. The source owes
    itself zero, and a past-ceiling crawl is a graph too large to
    walk dumbly.
    """
    if not graph.has_node(source):
        raise KeyError(f"{source!r} is not a node")
    found = {source: 0}
    for _sweep in range(MAX_SWEEPS):
        moved = False
        for head, cost in sorted(found.items()):
            for tail, weight in graph.neighbours(head):
                if tail not in found or cost + weight < found[tail]:
                    found[tail] = cost + weight
                    moved = True
        if not moved:
            return dict(sorted(found.items()))
    raise OracleError("the walker never rested: past the sweep ceiling")


def distance_table(graph: Graph) -> dict:
    """The whole reachable table: every source walked, the hops merged.

    (source, target) -> cost for every ordered pair the arrows carry,
    diagonals at zero, unreachable pairs simply absent - the walker
    omits what it cannot walk, and the table below must do the same.
    """
    table: dict = {}
    for source in graph.nodes():
        for reached, cost in walk_from(graph, source).items():
            table[(source, reached)] = cost
    return dict(sorted(table.items()))


def oracle_table(graph: Graph) -> dict:
    """The walker's whole table, answered slow: the matrix's promise."""
    return distance_table(graph)

"""The oracle: the dumb cut enumeration that never misses, only crawls slow.

The flow value this library sells is the one this oracle answers
as least: every subset of nodes holding the source and not the
sink is drawn, the capacities of the arcs crossing from inside to
outside are summed, and the least sum is the answer. No residual,
no search order, no cleverness - complete enumeration over small
networks, where small means the corpora ship nodes a subset walk
can survive.

The walker in solve.py must land on this least value, unit for
unit, on every network the corpora hold: max-flow equals min-cut,
and that equality is the product.

The oracle is the product. The walker is the way to afford it.
"""

from __future__ import annotations

from itertools import combinations

from .graph import Graph


class OracleError(ValueError):
    """A network the enumeration refuses to walk, or a shape it refuses."""

    __slots__ = ()


def cuts(graph: Graph, source: int, sink: int) -> list:
    """Every source-sink cut as (capacity, side); the dumb walk.

    The walk: draw every subset of the other nodes, add the source,
    and sum the capacities of the arcs leaving for the far shore.
    Exponential on purpose - the corpora are small so the walk
    finishes - and the answer it cannot give is the one worth
    having: a network with no route has a cut of zero.
    """
    if not graph.has_node(source):
        raise KeyError(f"{source!r} is not a node")
    if not graph.has_node(sink):
        raise KeyError(f"{sink!r} is not a node")
    if source == sink:
        raise OracleError(f"{source} is both ends: no subset separates it from itself")
    others = [node for node in graph.nodes() if node not in (source, sink)]
    arcs = graph.edges()
    drawn: list = []
    for size in range(len(others) + 1):
        for rest in combinations(others, size):
            side = {source} | set(rest)
            capacity = sum(room for (start, end), room in arcs
                           if start in side and end not in side)
            drawn.append((capacity, tuple(sorted(side))))
    return drawn


def min_cut(graph: Graph, source: int, sink: int) -> int:
    """The least capacity any source-sink cut carries.

    Enumerated, not searched: every separating subset is drawn and
    the crossing sums are compared. A network with no route from
    source to sink has a cut of zero, and zero is the honest
    least - not a refusal.
    """
    return min(capacity for capacity, _side in cuts(graph, source, sink))


def least_cut(graph: Graph, source: int, sink: int) -> tuple:
    """The least cut and the side that owes it: (capacity, side)."""
    return min(cuts(graph, source, sink), key=lambda drawn: (drawn[0], drawn[1]))


def cut_capacity(graph: Graph, side: object) -> int:
    """What a named shore pays: the capacities crossing out of it."""
    inside = set(side)
    return sum(room for (start, end), room in graph.edges()
               if start in inside and end not in inside)


def oracle_value(graph: Graph, source: int, sink: int) -> int:
    """The least cut, answered slow: the walker's promise."""
    return min_cut(graph, source, sink)

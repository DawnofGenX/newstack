"""The order: Kahn with a sorted ready-frontier, deterministic by rule.

order(graph) lists every node exactly once, predecessors before their
targets. The walk keeps a frontier of nodes with no unread predecessor
and hands up the smallest label on it, so the same graph answers the
same sequence in every run - determinism is the sorted frontier, not
luck.

A node is released only when its last predecessor has gone. A cycle
holds its nodes shut: order() refuses with the block named, because
the honest answer to a tangled graph is the tangle, never a shuffled
list pretending the tangle is not there.
"""

from __future__ import annotations

from .graph import Graph

MAX_STEPS = 4096


class OrderError(ValueError):
    """A graph this orderer refuses to list, or a listing it refuses to keep."""

    __slots__ = ()


def _ready(remaining: dict, unread: dict) -> list:
    """The remaining nodes no remaining predecessor still points at, sorted."""
    return sorted(node for node in remaining if not unread[node])


def order(graph: Graph) -> tuple:
    """Every node once, predecessors first - or the block named.

    Kahn's rule, the sorted frontier as the law: the smallest label
    whose predecessors have all gone goes next - a node is released
    only when its last predecessor has gone. Re-running on the same
    graph answers the same sequence; take the last ready node instead
    of the least and that promise dies with it.
    """
    remaining = {node: set(graph.predecessors(node)) for node in graph.nodes()}
    unread = {node: len(seat) for node, seat in remaining.items()}
    frontier = _ready(remaining, unread)
    listed: list = []
    steps = 0
    while frontier:
        steps += 1
        if steps > MAX_STEPS:
            raise OrderError("the walk spun past its step ceiling")
        node = frontier[0]
        del remaining[node]
        del unread[node]
        listed.append(node)
        for target in graph.successors(node):
            if target in unread and target in remaining:
                unread[target] = max(unread[target] - 1, 0)
        frontier = _ready(remaining, unread)
    if remaining:
        raise OrderError(f"the graph is tangled: {block(graph)} blocks the order")
    return tuple(listed)


def validate(graph: Graph, listed: tuple | list) -> list:
    """Name every way a listing fails its own shape; empty holds.

    Every node appears exactly once, and every edge's source appears
    before its target. The shipped validator the corpora and the
    suites walk: a listing that breaks here is not an order.
    """
    breaks: list = []
    seen = list(listed)
    if sorted(seen) != sorted(graph.nodes()):
        breaks.append("the listing misses a node or invents one")
    if len(seen) != len(set(seen)):
        breaks.append("a node is listed twice")
    for source, target in graph.edges():
        placed = source in seen and target in seen
        if placed and seen.index(source) >= seen.index(target):
            breaks.append(f"{source}>{target} points backward")
    return breaks


def block(graph: Graph) -> tuple:
    """The nodes a cycle holds shut - the block, smallest label first.

    Kahn stalls exactly on the tangled remainder: the block names
    what stays when the released have gone, an honest set, smallest
    label first. Empty on a graph that orders.
    """
    remaining = {node: set(graph.predecessors(node)) for node in graph.nodes()}
    unread = {node: len(seat) for node, seat in remaining.items()}
    frontier = _ready(remaining, unread)
    steps = 0
    while frontier:
        steps += 1
        if steps > MAX_STEPS:
            raise OrderError("the walk spun past its step ceiling")
        node = frontier[0]
        for target in graph.successors(node):
            if target in unread:
                unread[target] = max(unread[target] - 1, 0)
        del remaining[node]
        del unread[node]
        frontier = [
            candidate for candidate in _ready(remaining, unread) if candidate in remaining
        ]
    return tuple(sorted(remaining))

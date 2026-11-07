"""The grower: the frontier, the crossing edge, the tree that answers.

The rule this grower keeps, and the marker the detector looks for:
a node joins the tree once, through the cheapest crossing edge.
The grower carries a frontier of crossing edges; the frontier
hands up the cheapest entry - ties broken by lowest pair - that
entry's far node joins the tree once, and its out-edges join the
frontier. Weights are nonneg, and the tree it grows costs exactly
what the enumeration oracle answers as minimum, edge for edge, on
every graph the corpora hold.

spanning_tree(graph, start) answers the tree's edge set,
tree_cost(graph, start) answers its total. A disconnected graph
names the node the frontier ran out of - a tree over a graph in
pieces would be a lie.
"""

from __future__ import annotations

from .graph import Graph

MAX_STEPS = 4096


class TreeError(ValueError):
    """A graph the grower refuses to grow over, or a shape it refuses."""

    __slots__ = ()


def _crossing_min(frontier: frozenset) -> tuple:
    """The cheapest crossing edge, lowest pair first among equals.

    Cheapest means exactly that: the entry kept is the lowest
    weight, and equal weights pick the lowest pair, so the tree a
    graph earns is the same tree on every run. Take the dearest
    entry instead and the grower stops being Prim - it spans, but
    the cost drifts from the oracle's minimum.
    """
    chosen = None
    for edge in sorted(frontier):
        if chosen is None or edge[1] < chosen[1]:
            chosen = edge
    if chosen is None:
        raise TreeError("the frontier ran dry: the graph is in pieces")
    return chosen


def _frontier_of(graph: Graph, inside: set) -> frozenset:
    """Every edge crossing from inside to outside, pairs lowest-first.

    Rebuilt each step from the grower's own set: an edge whose far
    end already joined is no longer crossing, and a stale entry
    would re-cross a node already in the tree.
    """
    return frozenset(
        ((node, neighbour) if node <= neighbour else (neighbour, node), weight)
        for node in sorted(inside)
        for neighbour, weight in graph.neighbours(node)
        if neighbour not in inside
    )


def _grow(graph: Graph, start: int) -> tuple:
    """The tree's edges and the nodes the frontier admitted."""
    if not graph.has_node(start):
        raise KeyError(f"{start!r} is not a node")
    inside = {start}
    edges: set = set()
    steps = 0
    while len(inside) < len(graph):
        steps += 1
        if steps > MAX_STEPS:
            raise TreeError("the grower spun past its step ceiling")
        low, weight = _crossing_min(_frontier_of(graph, inside))
        arrival = low[1] if low[0] in inside else low[0]
        if arrival in inside:
            raise TreeError(f"{arrival} joined the tree twice")
        inside.add(arrival)
        edges.add((low, weight))
    if len(edges) != len(graph) - 1:
        raise TreeError(f"{len(edges)} edges for {len(graph)} nodes: not a tree")
    return frozenset(edges), inside


def spanning_tree(graph: Graph, start: int) -> frozenset:
    """The tree's edge set: frozenset of (sorted pair, weight).

    The grower's answer, and the oracle's minimum exactly: |V|-1
    edges, every node spanned once, the total equal to the least
    cost any spanning tree of the graph can carry. A disconnected
    graph raises - the frontier names the node it never reached.
    """
    edges, _ = _grow(graph, start)
    return edges


def tree_cost(graph: Graph, start: int) -> int:
    """The tree's total weight: the sum the edge set carries.

    The same growth as spanning_tree - the cost is the answer a
    caller wants without the set - and it equals the oracle's
    minimum on every graph the corpora hold.
    """
    return sum(weight for _, weight in spanning_tree(graph, start))


def audit(graph: Graph, start: int, edges: frozenset) -> list:
    """Name every way a tree fails its own shape; empty holds.

    The set holds |V|-1 edges, every edge is the graph's, every
    node is touched, and the touched nodes form one piece. The
    equal-oracle tests carry the deeper promise - this audit is
    the cheap shape check the grower owes its own answer.
    """
    breaks: list = []
    if len(edges) != len(graph) - 1:
        breaks.append(f"{len(edges)} edges: a tree of {len(graph)} owes {len(graph) - 1}")
    owned = {(edge_pair, weight) for edge_pair, weight in graph.edges()}
    touched: set = set()
    for edge_pair, weight in edges:
        if (edge_pair, weight) not in owned:
            breaks.append(f"{edge_pair}@{weight} is no edge of the graph")
        touched.update(edge_pair)
    for node in graph.nodes():
        if len(graph) > 1 and node not in touched:
            breaks.append(f"{node} is spanned by nothing")
    return breaks

"""The oracle: the dumb enumeration that never misses, only crawls slow.

The tree cost this library sells is the one this oracle answers as
minimum: every |V|-1 subset of the edge list is drawn, the subsets
that span every node exactly once are the spanning trees, and the
least total is the answer. No sorted list, no fragments, no
cleverness - complete enumeration over small graphs, where small
means the corpora ship nodes a subset walk can survive.

The walker in solve.py must land on this minimum, edge-sum for
edge-sum, on every graph the corpora hold. A disconnected graph
has no spanning tree at all, and the oracle says so.

The oracle is the product. The walker is the way to afford it.
"""

from __future__ import annotations

from itertools import combinations

from .graph import Graph


class OracleError(ValueError):
    """A graph the enumeration refuses to walk, or a shape it refuses."""

    __slots__ = ()


def _spans(chosen: tuple, nodes: tuple) -> bool:
    """True when the chosen edges span every node exactly once."""
    touched: set = set()
    for (low, high), _weight in chosen:
        touched.add(low)
        touched.add(high)
    if len(touched) != len(nodes):
        return False
    seen = {nodes[0]}
    queue = [nodes[0]]
    while queue:
        node = queue.pop()
        for (low, high), _weight in chosen:
            partner = high if low == node else low if high == node else None
            if partner is not None and partner not in seen:
                seen.add(partner)
                queue.append(partner)
    return len(seen) == len(nodes)


def spanning_trees(graph: Graph) -> list:
    """Every spanning tree, as the frozenset the enumeration drew.

    The dumb walk: draw |V|-1 edges from the edge list, keep the
    draws that span every node in one piece. Exponential on
    purpose - the corpora are small so the walk finishes.
    """
    nodes = graph.nodes()
    size = len(nodes)
    if size == 0:
        raise OracleError("an empty graph spans nothing")
    if size == 1:
        return [frozenset()]
    trees: list = []
    for chosen in combinations(graph.edges(), size - 1):
        if _spans(chosen, nodes):
            trees.append(frozenset(chosen))
    if not trees:
        raise OracleError(f"{graph.to_text()[:36]!r} is in pieces: no spanning tree")
    return trees


def tree_total(edges: frozenset) -> int:
    """The weight a drawn edge set carries."""
    return sum(weight for _pair, weight in edges)


def min_cost(graph: Graph) -> int:
    """The least total any spanning tree of the graph can carry.

    Enumerated, not walked: every tree is drawn and the totals are
    compared. A graph in pieces has no tree and raises - the
    minimum of nothing is not zero.
    """
    return min(tree_total(tree) for tree in spanning_trees(graph))


def oracle_cost(graph: Graph) -> int:
    """The minimum spanning cost, answered slow: the walker's promise."""
    return min_cost(graph)

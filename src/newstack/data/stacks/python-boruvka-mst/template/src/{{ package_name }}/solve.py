"""Boruvka's rule: every fragment reaches out through its own cheapest edge each round.

The rule this walker keeps, and the marker the detector looks for:
every fragment reaches through its own cheapest edge each round. A
round hands each fragment its cheapest outgoing edge, joins the
pairs those edges connect, and repeats until one fragment stands;
the edge set a graph earns is the same set on every run. Take the
dearest edge for a fragment instead of the cheapest and the product
stops being Boruvka; stop a round before one fragment stands and
the tree comes out short.
"""
from __future__ import annotations

from .graph import Graph

MAX_ROUNDS = 64


class TreeError(ValueError):
    """A graph the walker refuses to walk, or a shape it refuses."""

    __slots__ = ()


class Fragment:
    """The fragments the walk keeps, joined never split.

    Fragment identity is the lowest label inside: a fresh node
    stands alone, a join hands the higher root to the lower, so
    two nodes sit in one fragment exactly when find() answers the
    same label for both.
    """

    __slots__ = ("_parent",)

    def __init__(self, nodes: tuple) -> None:
        self._parent = {node: node for node in nodes}

    def find(self, node: int) -> int:
        root = node
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[node] != root:
            self._parent[node], node = root, self._parent[node]
        return root

    def join(self, a: int, b: int) -> None:
        low, high = sorted((self.find(a), self.find(b)))
        self._parent[high] = low

    def one_piece(self) -> bool:
        return len({self.find(node) for node in self._parent}) == 1

    def component_count(self) -> int:
        return len({self.find(node) for node in self._parent})


def _weights(graph: Graph) -> dict:
    return {pair: weight for pair, weight in graph.edges()}


def _cheap_outgoing(graph: Graph, fragments: Fragment) -> dict:
    """For each fragment, its cheapest outgoing edge: (weight, pair)."""
    best: dict = {}
    for pair, weight in graph.edges():
        a, b = pair
        ra, rb = fragments.find(a), fragments.find(b)
        if ra == rb:
            continue
        for root in (ra, rb):
            if root not in best or (weight, pair) < best[root]:
                best[root] = (weight, pair)
    return best


def _run(graph: Graph) -> tuple:
    """Boruvka's rounds: each fragment reaches through its cheapest edge.

    Returns (taken edge set, tuple of per-round frozensets of edges
    added that round).
    """
    fragments = Fragment(graph.nodes())
    weights = _weights(graph)
    taken: set = set()
    round_records: list = []
    rounds = 0
    while not fragments.one_piece():
        best = _cheap_outgoing(graph, fragments)
        if not best:
            raise TreeError("the walk ran out of edges: the graph is in pieces")
        candidates = {pair for (_w, pair) in best.values()}
        applied: set = set()
        for pair in sorted(candidates):
            a, b = pair
            if fragments.find(a) == fragments.find(b):
                continue
            fragments.join(a, b)
            taken.add((pair, weights[pair]))
            applied.add((pair, weights[pair]))
            if len(taken) > len(graph.nodes()) - 1:
                break
        if not applied:
            raise TreeError("a round joined nothing: the graph is in pieces")
        round_records.append(frozenset(applied))
        rounds += 1
        if rounds > MAX_ROUNDS:
            raise TreeError("the walk spun past its round ceiling")
    if len(graph) > 1 and len(taken) != len(graph) - 1:
        raise TreeError(f"{len(taken)} edges for {len(graph)} nodes: not a tree")
    return frozenset(taken), tuple(round_records)


def spanning_tree(graph: Graph) -> frozenset:
    """The tree's edge set: frozenset of (sorted pair, weight)."""
    edges, _rounds = _run(graph)
    return edges


def tree_cost(graph: Graph) -> int:
    """The tree's total weight."""
    return sum(weight for _edge_pair, weight in spanning_tree(graph))


def rounds(graph: Graph) -> tuple:
    """The honest per-round record: a tuple of frozensets, one per round."""
    _edges, record = _run(graph)
    return record


def audit(graph: Graph, edges: frozenset) -> list:
    """Name every way a tree fails its own shape; empty holds."""
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
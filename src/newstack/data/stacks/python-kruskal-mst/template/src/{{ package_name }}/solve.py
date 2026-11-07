"""The walker: one sorted list, the fragments, the tree that answers.

The rule this walker keeps, and the marker the detector looks for:
the sorted walk joins fragments and refuses cycles. The edges are
sorted once - weight first, lowest pair among equals - and the
walk considers them in that nondecreasing order; an edge joins two
fragments when its ends sit in different ones, and is refused when
it would close a cycle over fragments already joined.

spanning_tree(graph) answers the tree's edge set, tree_cost(graph)
answers its total, witness(graph) answers the honest per-edge
record of taken-or-skipped with the reason. Weights are nonneg,
and the tree it walks costs exactly what the enumeration oracle
answers as minimum, edge for edge, on every graph the corpora
hold. A disconnected graph names the pieces it cannot join - a
tree over a graph in pieces would be a lie.
"""

from __future__ import annotations

from .graph import Graph

MAX_STEPS = 4096


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


class Step:
    """One edge's honest record: the edge, its answer, its reason."""

    __slots__ = ("edge", "reason", "taken", "weight")

    def __init__(self, edge: tuple, weight: int, taken: bool, reason: str) -> None:
        self.edge = edge
        self.weight = weight
        self.taken = taken
        self.reason = reason

    def __repr__(self) -> str:
        return f"Step({self.edge}, {self.weight}, {self.taken}, {self.reason!r})"

    def to_record(self) -> dict:
        return {"edge": list(self.edge), "weight": self.weight,
                "taken": self.taken, "reason": self.reason}


def _walk(graph: Graph) -> tuple:
    """The sorted walk: the taken edges and every edge's record.

    The list is sorted once - weight first, lowest pair among
    equals - so the tie-break is documented and the edge set a
    graph earns is the same set on every run. Take an edge that
    closes a cycle instead of refusing it and the product stops
    being a tree; skip the lightest edge of a tie and the answer
    drifts from the enumeration's minimum.
    """
    fragments = Fragment(graph.nodes())
    taken: set = set()
    steps: list = []
    considered = 0
    for edge_pair, weight in sorted(graph.edges(), key=lambda item: (item[1], item[0])):
        considered += 1
        if considered > MAX_STEPS:
            raise TreeError("the walk spun past its step ceiling")
        low, high = edge_pair
        if fragments.find(low) == fragments.find(high):
            steps.append(Step(edge_pair, weight, False, "closes a cycle"))
            continue
        fragments.join(low, high)
        taken.add((edge_pair, weight))
        steps.append(Step(edge_pair, weight, True, "joins fragments"))
    if len(graph) > 1 and not fragments.one_piece():
        raise TreeError("the walk ran out of edges: the graph is in pieces")
    if len(taken) != len(graph) - 1:
        raise TreeError(f"{len(taken)} edges for {len(graph)} nodes: not a tree")
    return frozenset(taken), tuple(steps)


def spanning_tree(graph: Graph) -> frozenset:
    """The tree's edge set: frozenset of (sorted pair, weight).

    The walker's answer, and the oracle's minimum exactly: |V|-1
    edges, every node spanned once, the total equal to the least
    cost any spanning tree of the graph can carry. A disconnected
    graph raises - the walk names the pieces it never joined.
    """
    edges, _steps = _walk(graph)
    return edges


def tree_cost(graph: Graph) -> int:
    """The tree's total weight: the sum the edge set carries.

    The same walk as spanning_tree - the cost is the answer a
    caller wants without the set - and it equals the oracle's
    minimum on every graph the corpora hold.
    """
    return sum(weight for _edge_pair, weight in spanning_tree(graph))


def witness(graph: Graph) -> tuple:
    """The honest per-edge record of the walk: taken-or-skipped, reasoned.

    One Step per owned edge, in the order the sorted list handed
    them - nondecreasing weight, lowest pair among equals - each
    saying joins fragments or closes a cycle. The product is the
    walk; this is its ledger.
    """
    _edges, steps = _walk(graph)
    return steps


def audit(graph: Graph, edges: frozenset) -> list:
    """Name every way a tree fails its own shape; empty holds.

    The set holds |V|-1 edges, every edge is the graph's, every
    node is touched, and the touched nodes form one piece. The
    equal-oracle tests carry the deeper promise - this audit is
    the cheap shape check the walker owes its own answer.
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

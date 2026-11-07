"""The small directed graph: integer labels, spoken weights, noise refused.

A graph is a bounded set of small integer nodes and the weighted
arrows between them. add_node admits a label, add_edge admits a
source, a target, and a nonneg integer weight. The graph is a
digraph: an edge points from its source to its target and is held
in that one direction only, so edges() answers ordered pairs and
every walk owes its arrows.

The marker the detector looks for lives in solve.py; this module is
the door the graphs pass on their way in.
"""

from __future__ import annotations

MAX_NODES = 32
MAX_LABEL = 999


class GraphError(ValueError):
    """A label, a weight, or an edge the graph refuses to hold."""

    __slots__ = ()


def ensure_label(value: object) -> int:
    """Answer the integer a label names, or refuse it."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise GraphError(f"{value!r} is not an integer label")
    if not 0 <= value <= MAX_LABEL:
        raise GraphError(f"{value} is past the {MAX_LABEL} label ceiling")
    return value


def ensure_weight(value: object) -> int:
    """Answer the integer a weight speaks, or refuse it."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise GraphError(f"{value!r} is not an integer weight")
    if value < 0:
        raise GraphError(f"{value} is negative: every weight must be nonneg")
    if value > MAX_LABEL:
        raise GraphError(f"{value} is past the {MAX_LABEL} weight ceiling")
    return value


def hop(source: int, target: int) -> tuple:
    """The edge's ordered ends: an arrow points, so the pair is ordered."""
    return (source, target)


class Graph:
    """A small integer-keyed weighted digraph with a fixed face.

    add_edge stores the arrow in its one direction - the graph is
    directed and says so plainly - and edges() answers every arrow
    once, keyed by its (source, target) pair, lowest first.
    """

    __slots__ = ("_adj",)

    def __init__(self) -> None:
        self._adj: dict = {}

    def add_node(self, node: int) -> Graph:
        label = ensure_label(node)
        if label not in self._adj and len(self._adj) >= MAX_NODES:
            raise GraphError(f"no room: {MAX_NODES} nodes is the ceiling")
        self._adj.setdefault(label, {})
        return self

    def add_edge(self, source: int, target: int, weight: int) -> Graph:
        tail = ensure_label(source)
        head = ensure_label(target)
        if tail == head:
            raise GraphError(f"{source} is a loop: an arrow owes two distinct ends")
        cost = ensure_weight(weight)
        self.add_node(tail)
        self.add_node(head)
        self._adj[tail][head] = cost
        return self

    def has_node(self, node: int) -> bool:
        return node in self._adj

    def nodes(self) -> tuple:
        """Every node, smallest label first."""
        return tuple(sorted(self._adj))

    def neighbours(self, node: int) -> tuple:
        """The node's out-arrows, target first, as (target, weight) pairs."""
        if node not in self._adj:
            raise GraphError(f"{node!r} is not a node")
        return tuple(sorted(self._adj[node].items()))

    def edges(self) -> tuple:
        """Every arrow once: ((source, target), weight), lowest pair first.

        The pair is ordered - an arrow points from its source to its
        target - and each arrow appears exactly once, keyed by the
        direction it was given.
        """
        owned: dict = {}
        for source, targets in self._adj.items():
            for target, weight in targets.items():
                owned[hop(source, target)] = weight
        return tuple(sorted((edge_pair, weight)
                            for edge_pair, weight in owned.items()))

    def to_text(self) -> str:
        """The graph as tokens: bare labels are nodes, A>B=W is an arrow."""
        parts = [str(node) for node in self.nodes()]
        parts += [f"{source}>{target}={weight}" for (source, target), weight in self.edges()]
        return " ".join(parts)

    def __len__(self) -> int:
        return len(self._adj)


def _label(text: str, token: str) -> int:
    try:
        return ensure_label(int(text))
    except ValueError:
        raise GraphError(f"{token!r} holds {text!r}, no integer label") from None


def _weight(text: str, token: str) -> int:
    try:
        return ensure_weight(int(text))
    except ValueError:
        raise GraphError(f"{token!r} holds {text!r}, no nonneg integer weight") from None


def parse_graph(text: str) -> Graph:
    """Tokens in, a digraph out: '1 2 1>2=4' is two nodes, one arrow.

    Bare labels declare nodes, A>B=W declares a weighted arrow from A
    to B (and admits both ends); A>B without a weight speaks no cost
    and is refused, because a silent default is how wrong tables get
    shipped. A>B points one way: B is no way back.
    """
    tokens = text.split()
    if not tokens:
        raise GraphError("no tokens: an empty line names no graph")
    graph = Graph()
    for token in tokens:
        if ">" in token:
            head, _, tail = token.partition(">")
            target, _, weight = tail.partition("=")
            if not weight:
                raise GraphError(f"{token!r} speaks no weight: every arrow owes A>B=W")
            graph.add_edge(_label(head, token), _label(target, token), _weight(weight, token))
            continue
        graph.add_node(_label(token, token))
    return graph

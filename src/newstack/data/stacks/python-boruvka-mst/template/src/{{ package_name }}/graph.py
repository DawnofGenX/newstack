"""The small undirected graph: integer labels, spoken weights, noise refused.

A graph is a bounded set of small integer nodes and the weighted
edges between them. add_node admits a label, add_edge admits a pair
and a nonneg integer weight. The edges are owned once: the graph
keeps each edge exactly once, keyed by its lowest-first pair, and
adjacency is answered from that ownership - an undirected edge has
no arrow to duplicate.

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


def pair(a: int, b: int) -> tuple:
    """The edge's endpoints, lowest label first: the pair is directionless."""
    return (a, b) if a <= b else (b, a)


class Graph:
    """A small integer-keyed weighted undirected graph with a fixed face.

    The edges are owned once - a dict keyed by the lowest-first
    pair - and adjacency is answered from that ownership, so no
    direction can double an edge and no walk can see one twice.
    """

    __slots__ = ("_edges", "_nodes")

    def __init__(self) -> None:
        self._nodes: set = set()
        self._edges: dict = {}

    def add_node(self, node: int) -> Graph:
        label = ensure_label(node)
        if label not in self._nodes and len(self._nodes) >= MAX_NODES:
            raise GraphError(f"no room: {MAX_NODES} nodes is the ceiling")
        self._nodes.add(label)
        return self

    def add_edge(self, a: int, b: int, weight: int) -> Graph:
        source = ensure_label(a)
        target = ensure_label(b)
        if source == target:
            raise GraphError(f"{a} is a loop: an edge owes two distinct ends")
        cost = ensure_weight(weight)
        self.add_node(source)
        self.add_node(target)
        self._edges[pair(source, target)] = cost
        return self

    def has_node(self, node: int) -> bool:
        return node in self._nodes

    def nodes(self) -> tuple:
        """Every node, smallest label first."""
        return tuple(sorted(self._nodes))

    def neighbours(self, node: int) -> tuple:
        """The node's doors, neighbour first, as (neighbour, weight) pairs."""
        if node not in self._nodes:
            raise GraphError(f"{node!r} is not a node")
        return tuple(sorted(
            (high if low == node else low, weight)
            for (low, high), weight in self._edges.items()
            if node in (low, high)
        ))

    def edges(self) -> tuple:
        """Every edge once: (pair, weight), lowest pair first.

        The edge is owned exactly once by the graph - the walk's
        sorted list has one entry per owned edge, and no direction
        can answer it a second time.
        """
        return tuple(sorted(self._edges.items()))

    def to_text(self) -> str:
        """The graph as tokens: bare labels are nodes, A>B=W is an edge."""
        parts = [str(node) for node in self.nodes()]
        parts += [f"{low}>{high}={weight}" for (low, high), weight in self.edges()]
        return " ".join(parts)

    def __len__(self) -> int:
        return len(self._nodes)


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
    """Tokens in, a weighted graph out: '1 2 1>2=4' is two nodes, one edge.

    Bare labels declare nodes, A>B=W declares a weighted edge (and
    both ends); A>B without a weight speaks no cost and is refused,
    because a silent default is how wrong trees get shipped.
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
                raise GraphError(f"{token!r} speaks no weight: every edge owes A>B=W")
            graph.add_edge(_label(head, token), _label(target, token), _weight(weight, token))
            continue
        graph.add_node(_label(token, token))
    return graph

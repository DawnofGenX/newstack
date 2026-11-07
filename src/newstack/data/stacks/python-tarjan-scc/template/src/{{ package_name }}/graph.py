"""The graph: integer labels in, adjacency out, noise refused.

A graph is a bounded set of small integer nodes and the edges between
them. add_node admits a label, add_edge admits a pair, and every
answer the library gives sorts what it walks - successors, edges,
nodes - so a walk never depends on insertion order.

The marker the detector looks for lives in scc.py; this module is
the door the graphs pass on their way in.
"""

from __future__ import annotations

MAX_NODES = 64
MAX_LABEL = 999


class GraphError(ValueError):
    """A label, a node, or an edge the graph refuses to hold."""

    __slots__ = ()


def ensure_label(value: object) -> int:
    """Answer the integer a label names, or refuse it."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise GraphError(f"{value!r} is not an integer label")
    if not 0 <= value <= MAX_LABEL:
        raise GraphError(f"{value} is past the {MAX_LABEL} label ceiling")
    return value


class Graph:
    """A small integer-keyed digraph with a deterministic face."""

    __slots__ = ("_out",)

    def __init__(self) -> None:
        self._out: dict = {}

    def add_node(self, node: int) -> Graph:
        label = ensure_label(node)
        if label not in self._out and len(self._out) >= MAX_NODES:
            raise GraphError(f"no room: {MAX_NODES} nodes is the ceiling")
        self._out.setdefault(label, set())
        return self

    def add_edge(self, source: int, target: int) -> Graph:
        self.add_node(source)
        self.add_node(target)
        self._out[source].add(target)
        return self

    def has_node(self, node: int) -> bool:
        return node in self._out

    def nodes(self) -> tuple:
        """Every node, smallest label first."""
        return tuple(sorted(self._out))

    def successors(self, node: int) -> tuple:
        if node not in self._out:
            raise GraphError(f"{node!r} is not a node")
        return tuple(sorted(self._out[node]))

    def edges(self) -> tuple:
        """Every edge, source then target, smallest first."""
        return tuple(
            (source, target)
            for source in sorted(self._out)
            for target in sorted(self._out[source])
        )

    def to_text(self) -> str:
        """The graph as tokens: bare labels are nodes, A>B is an edge."""
        parts = [str(node) for node in self.nodes()]
        parts += [f"{source}>{target}" for source, target in self.edges()]
        return " ".join(parts)

    def __len__(self) -> int:
        return len(self._out)


def _label(text: str, token: str) -> int:
    try:
        return ensure_label(int(text))
    except ValueError:
        raise GraphError(f"{token!r} holds {text!r}, no integer label") from None


def parse_graph(text: str) -> Graph:
    """Tokens in, a graph out: '1 2 1>3' is two nodes and one edge.

    Bare labels declare nodes, A>B declares an edge (and both ends).
    Every token must be an integer or an arrow between integers.
    """
    tokens = text.split()
    if not tokens:
        raise GraphError("no tokens: an empty line names no graph")
    graph = Graph()
    for token in tokens:
        if ">" in token:
            head, _, tail = token.partition(">")
            graph.add_edge(_label(head, token), _label(tail, token))
            continue
        graph.add_node(_label(token, token))
    return graph

"""The weighted graph: integer labels, spoken weights, noise refused.

A graph is a bounded set of small integer nodes and the weighted
edges between them. add_node admits a label, add_edge admits a pair
and a nonneg integer weight, and every answer the library gives
sorts what it walks - successors, edges, nodes - so a walk never
depends on insertion order.

The marker the detector looks for lives in solve.py; this module is
the door the graphs pass on their way in.
"""

from __future__ import annotations

MAX_NODES = 64
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


class Graph:
    """A small integer-keyed weighted digraph with a deterministic face."""

    __slots__ = ("_out",)

    def __init__(self) -> None:
        self._out: dict = {}

    def add_node(self, node: int) -> Graph:
        label = ensure_label(node)
        if label not in self._out and len(self._out) >= MAX_NODES:
            raise GraphError(f"no room: {MAX_NODES} nodes is the ceiling")
        self._out.setdefault(label, {})
        return self

    def add_edge(self, source: int, target: int, weight: int) -> Graph:
        self.add_node(source)
        self.add_node(target)
        self._out[source][target] = ensure_weight(weight)
        return self

    def has_node(self, node: int) -> bool:
        return node in self._out

    def nodes(self) -> tuple:
        """Every node, smallest label first."""
        return tuple(sorted(self._out))

    def successors(self, node: int) -> tuple:
        """The node's out-edges, target first, as (target, weight) pairs."""
        if node not in self._out:
            raise GraphError(f"{node!r} is not a node")
        return tuple(sorted(self._out[node].items()))

    def edges(self) -> tuple:
        """Every edge, source then target, smallest first, with its weight."""
        return tuple(
            (source, target, weight)
            for source in sorted(self._out)
            for target, weight in sorted(self._out[source].items())
        )

    def to_text(self) -> str:
        """The graph as tokens: bare labels are nodes, A>B=W is an edge."""
        parts = [str(node) for node in self.nodes()]
        parts += [f"{source}>{target}={weight}" for source, target, weight in self.edges()]
        return " ".join(parts)

    def __len__(self) -> int:
        return len(self._out)


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
    both ends). The weight is never implicit: 'A>B' speaks no cost
    and is refused, because a silent default weight is how wrong
    routes get shipped.
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
            source = _label(head, token)
            graph.add_edge(source, _label(target, token), _weight(weight, token))
            continue
        graph.add_node(_label(token, token))
    return graph

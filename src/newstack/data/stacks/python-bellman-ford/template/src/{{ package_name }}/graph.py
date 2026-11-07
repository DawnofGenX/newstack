"""The weighted graph: integer labels, integer weights, noise refused.

A graph is a bounded set of small integer nodes and the weighted edges
between them. add_node admits a label, add_edge(source, target, weight)
admits a weighted pair, and every answer the library gives sorts what it
walks - nodes, edges, successors - so a walk never depends on insertion
order. Weights may be negative; that is the whole point of the walker.

The marker the detector looks for lives in walk.py; this module is the
door the weighted graphs pass on their way in.
"""

from __future__ import annotations

MAX_NODES = 64
MAX_LABEL = 999
MAX_WEIGHT = 999

UNREACHED = None


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
    """Answer the integer a weight names - negative allowed - or refuse it."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise GraphError(f"{value!r} is not an integer weight")
    if -MAX_WEIGHT <= value <= MAX_WEIGHT:
        return value
    raise GraphError(f"{value} is past the {MAX_WEIGHT} weight ceiling")


class Graph:
    """A small integer-keyed digraph with integer weights and a sorted face."""

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
        if node not in self._out:
            raise GraphError(f"{node!r} is not a node")
        return tuple(sorted(self._out[node]))

    def weight(self, source: int, target: int) -> int:
        if target not in self._out.get(source, {}):
            raise GraphError(f"no edge from {source} to {target}")
        return self._out[source][target]

    def edges(self) -> tuple:
        """Every edge, source then target, smallest first, weight last."""
        return tuple(
            (source, target, weight)
            for source in sorted(self._out)
            for target, weight in sorted(self._out[source].items())
        )

    def to_text(self) -> str:
        """The graph as tokens: bare labels are nodes, A>B=W is a weighted edge."""
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
        raise GraphError(f"{token!r} holds {text!r}, no integer weight") from None


def parse_graph(text: str) -> Graph:
    """Tokens in, a weighted graph out: '1 2 1>3=-4' is two nodes, one edge.

    Bare labels declare nodes, A>B=W declares a weighted edge (and admits
    both ends). Every edge token must carry its weight; a bare A>B is
    refused because an unweighted edge is not this tool's subject.
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
                raise GraphError(f"{token!r} is an edge with no weight")
            graph.add_edge(_label(head, token), _label(target, token), _weight(weight, token))
            continue
        graph.add_node(_label(token, token))
    return graph

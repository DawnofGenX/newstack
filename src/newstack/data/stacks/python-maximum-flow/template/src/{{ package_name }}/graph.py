"""The small digraph: integer labels, spoken capacities, noise refused.

A network is a bounded set of small integer nodes and the capacityed
arcs between them. add_node admits a label, add_edge(source, target,
capacity) admits a directed arc with a nonneg integer capacity. The
graph is directed: every arc is stored under its own direction only,
and a pair of nodes holds one channel - a repeated arc merges its
capacity into the standing channel, and the opposite arc of a
standing arc is refused at the door.

The marker the detector looks for lives in solve.py; this module is
the door the networks pass on their way in.
"""

from __future__ import annotations

MAX_NODES = 32
MAX_LABEL = 999


class GraphError(ValueError):
    """A label, a capacity, or an arc the network refuses to hold."""

    __slots__ = ()


def ensure_label(value: object) -> int:
    """Answer the integer a label names, or refuse it."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise GraphError(f"{value!r} is not an integer label")
    if not 0 <= value <= MAX_LABEL:
        raise GraphError(f"{value} is past the {MAX_LABEL} label ceiling")
    return value


def ensure_capacity(value: object) -> int:
    """Answer the integer a capacity speaks, or refuse it."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise GraphError(f"{value!r} is not an integer capacity")
    if value < 0:
        raise GraphError(f"{value} is negative: every capacity must be nonneg")
    if value > MAX_LABEL:
        raise GraphError(f"{value} is past the {MAX_LABEL} capacity ceiling")
    return value


class Graph:
    """A small integer-keyed directed capacity network with a fixed face.

    add_edge stores the arc under its own direction only - the graph
    is directed and says so plainly - and a pair of nodes holds one
    channel: a repeated arc merges its capacity into the channel
    already standing, and the opposite arc of a standing arc is
    refused, because two-way channels let a walker cancel its own
    tracks. edges() answers every arc once, lowest source first.
    """

    __slots__ = ("_out",)

    def __init__(self) -> None:
        self._out: dict = {}

    def add_node(self, node: int) -> Graph:
        label = ensure_label(node)
        if label not in self._out and len(self._out) >= MAX_NODES:
            raise GraphError(f"no room: {MAX_NODES} nodes is the ceiling")
        self._out.setdefault(label, {})
        return self

    def add_edge(self, source: int, target: int, capacity: int) -> Graph:
        start = ensure_label(source)
        end = ensure_label(target)
        if start == end:
            raise GraphError(f"{source} is a loop: an arc owes two distinct ends")
        room = ensure_capacity(capacity)
        self.add_node(start)
        self.add_node(end)
        if start in self._out[end]:
            raise GraphError(
                f"{start}>{end} with {end}>{start} stands: one pair, one channel"
            )
        merged = self._out[start].get(end, 0) + room
        if merged > MAX_LABEL:
            raise GraphError(
                f"{merged} merges past the {MAX_LABEL} capacity ceiling"
            )
        self._out[start][end] = merged
        return self

    def has_node(self, node: int) -> bool:
        return node in self._out

    def nodes(self) -> tuple:
        """Every node, smallest label first."""
        return tuple(sorted(self._out))

    def out_arcs(self, node: int) -> tuple:
        """The node's out-arcs, target first, as (target, capacity) pairs."""
        if node not in self._out:
            raise GraphError(f"{node!r} is not a node")
        return tuple(sorted(self._out[node].items()))

    def in_arcs(self, node: int) -> tuple:
        """The node's in-arcs, source first, as (source, capacity) pairs."""
        if node not in self._out:
            raise GraphError(f"{node!r} is not a node")
        return tuple(sorted((start, caps[node]) for start, caps in self._out.items()
                            if node in caps))

    def edges(self) -> tuple:
        """Every arc once: ((source, target), capacity), lowest source first."""
        return tuple(sorted(((start, end), room)
                            for start, caps in self._out.items()
                            for end, room in caps.items()))

    def to_text(self) -> str:
        """The network as tokens: bare labels are nodes, A>B=W is an arc."""
        parts = [str(node) for node in self.nodes()]
        parts += [f"{start}>{end}={room}" for (start, end), room in self.edges()]
        return " ".join(parts)

    def __len__(self) -> int:
        return len(self._out)


def _label(text: str, token: str) -> int:
    try:
        return ensure_label(int(text))
    except ValueError:
        raise GraphError(f"{token!r} holds {text!r}, no integer label") from None


def _capacity(text: str, token: str) -> int:
    try:
        return ensure_capacity(int(text))
    except ValueError:
        raise GraphError(f"{token!r} holds {text!r}, no nonneg integer capacity") from None


def parse_graph(text: str) -> Graph:
    """Tokens in, a directed network out: '1 2 1>2=4' is two nodes, one arc.

    Bare labels declare nodes, A>B=W declares a capacityed arc (and
    admits both ends); A>B without a capacity speaks no room and is
    refused, because a silent default is how wrong shipments ship.
    A repeated arc merges into the standing channel; the opposite
    arc of a standing arc is refused at the door.
    """
    tokens = text.split()
    if not tokens:
        raise GraphError("no tokens: an empty line names no network")
    graph = Graph()
    for token in tokens:
        if ">" in token:
            head, _, tail = token.partition(">")
            target, _, capacity = tail.partition("=")
            if not capacity:
                raise GraphError(f"{token!r} speaks no capacity: every arc owes A>B=W")
            graph.add_edge(_label(head, token), _label(target, token),
                           _capacity(capacity, token))
            continue
        graph.add_node(_label(token, token))
    return graph

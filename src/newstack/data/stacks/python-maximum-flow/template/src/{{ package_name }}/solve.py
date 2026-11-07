"""The walker: the residual, the augmenting path, the flow that answers.

The rule this walker keeps, and the marker the detector looks for:
flow walks the residual, never past a bottleneck. The walker runs
Breadth-First Search over the residual network, takes the shortest
augmenting path it finds, pushes that path\'s bottleneck (an
integer, since every capacity is), and repeats until the search
cannot reach the sink. Capacities are nonneg integers and the flow
it lands on is an integer too.

max_flow(graph, source, sink) answers the value;
flow_map(graph, source, sink) answers the shipped amount per arc.
The value equals the least cut the brute-force oracle can name -
max-flow equals min-cut - on every network the corpora hold, and
the shipped map conserves at every interior node and never walks
past a capacity.
"""

from __future__ import annotations

from itertools import pairwise

from .graph import Graph

MAX_STEPS = 4096


class FlowError(ValueError):
    """A network the walker refuses to walk, or a shape it refuses."""

    __slots__ = ()


def _residual(graph: Graph) -> dict:
    """The walker\'s scratch: capacity left per arc, reverse room included.

    Every real arc starts with its full capacity left; every reverse
    direction starts at zero unless the opposite arc is real too, so
    cancelling shipped flow is always a legal step of the walk.
    """
    room: dict = {node: {} for node in graph.nodes()}
    for (start, end), capacity in graph.edges():
        room[start][end] = capacity
        room[end].setdefault(start, 0)
    return room


def _path_to_sink(room: dict, source: int, sink: int):
    """The shortest residual path, breadth first, or None.

    Breadth first on purpose - Edmonds-Karp is Ford-Fulkerson with
    this search - and ties walk the lowest label first, so the same
    network walks to the same answer on every run.
    """
    seen = {source}
    back: dict = {}
    queue = [source]
    while queue:
        node = queue.pop(0)
        if node == sink:
            trail = [sink]
            while trail[-1] != source:
                trail.append(back[trail[-1]])
            return tuple(reversed(trail))
        for neighbour, left in sorted(room[node].items()):
            if left > 0 and neighbour not in seen:
                seen.add(neighbour)
                back[neighbour] = node
                queue.append(neighbour)
    return None


def _ship(graph: Graph, source: int, sink: int) -> tuple:
    """The shipped map and the value, walked to the last augment."""
    if not graph.has_node(source):
        raise KeyError(f"{source!r} is not a node")
    if not graph.has_node(sink):
        raise KeyError(f"{sink!r} is not a node")
    if source == sink:
        raise FlowError(f"{source} is both ends: flow needs two distinct ends")
    room = _residual(graph)
    shipped = {(start, end): 0 for (start, end), _capacity in graph.edges()}
    steps = 0
    while True:
        trail = _path_to_sink(room, source, sink)
        if trail is None:
            break
        steps += 1
        if steps > MAX_STEPS:
            raise FlowError("the walker spun past its step ceiling")
        bottleneck = min(room[head][tail] for head, tail in pairwise(trail))
        for head, tail in pairwise(trail):
            room[head][tail] -= bottleneck
            room[tail][head] = room[tail].get(head, 0) + bottleneck
            if (head, tail) in shipped:
                shipped[(head, tail)] += bottleneck
            if (tail, head) in shipped:
                shipped[(tail, head)] -= bottleneck
    value = sum(amount for (start, _end), amount in shipped.items() if start == source)
    return shipped, value


def max_flow(graph: Graph, source: int, sink: int) -> int:
    """The value the network carries from source to sink.

    The Edmonds-Karp answer, and it equals the brute-force oracle\'s
    least cut exactly, on every network the corpora hold. A network
    with no route from source to sink carries zero, which is the
    honest answer, not a refusal.
    """
    _shipped, value = _ship(graph, source, sink)
    return value


def flow_map(graph: Graph, source: int, sink: int) -> dict:
    """The shipped amount per arc: {(source, target): amount}.

    Every key is an arc of the network, every amount sits between
    zero and that arc\'s capacity, and every interior node hands on
    exactly what it took in. The map is the flow; the value is what
    the source let go.
    """
    shipped, _value = _ship(graph, source, sink)
    return dict(shipped)


def audit(graph: Graph, source: int, sink: int, shipped: dict) -> list:
    """Name every way a shipped map fails its own shape; empty holds.

    Every key is the network\'s arc, every amount respects its
    capacity, every interior node hands on what it received, and
    the source\'s outgo is the sink\'s income. The equal-oracle
    tests carry the deeper promise - this audit is the cheap shape
    check the walker owes its own answer.
    """
    breaks: list = []
    owned = {(start, end): capacity for (start, end), capacity in graph.edges()}
    for arc, amount in shipped.items():
        if arc not in owned:
            breaks.append(f"{arc} is no arc of the network")
        elif not 0 <= amount <= owned[arc]:
            breaks.append(f"{arc} shipped {amount} past its {owned[arc]}")
    for arc in owned:
        if arc not in shipped:
            breaks.append(f"{arc} is missing from the map")
    for node in graph.nodes():
        if node in (source, sink):
            continue
        taken = sum(amount for (_s, end), amount in shipped.items() if end == node)
        gave = sum(amount for (start, _e), amount in shipped.items() if start == node)
        if taken != gave:
            breaks.append(f"{node} took {taken} and gave {gave}: not conserved")
    out = sum(amount for (start, _end), amount in shipped.items() if start == source)
    in_ = sum(amount for (_start, end), amount in shipped.items() if end == sink)
    if out != in_:
        breaks.append(f"source gave {out}, sink took {in_}: the value leaks")
    return breaks

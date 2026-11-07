"""The oracle: the dumb walk-count that never misses, only crawls slow.

The distance map this library sells is the one this oracle answers:
every walk out of the source of at most |V|-1 edges, counted layer by
layer - exactly-k edges per layer - and the cheapest total kept.
Walks may revisit nodes on the way in; with no reachable cycle
dragging a total down, the cheapest answer still fits inside |V|-1
edges, so the count is complete.

The oracle is the product. The walker in walk.py is the way to afford it.
"""

from __future__ import annotations

from .graph import UNREACHED, Graph, GraphError


def oracle_distances(graph: Graph, source: int) -> dict:
    """node -> the cheapest walk cost, answered by counting alone.

    Layer by layer over walks of exactly k edges, k up to len(graph)
    - 1; every layer merges duplicates by cost and every total the
    walks ever touch is kept. Nodes no walk reaches answer UNREACHED.
    """
    if not graph.has_node(source):
        raise GraphError(f"{source!r} is not a node, so no walk starts there")
    best: dict = dict.fromkeys(graph.nodes(), UNREACHED)
    best[source] = 0
    frontier = {source: 0}
    for _ in range(max(len(graph) - 1, 0)):
        layer: dict = {}
        for node, cost in frontier.items():
            for target in graph.successors(node):
                step = cost + graph.weight(node, target)
                if target not in layer or step < layer[target]:
                    layer[target] = step
        if not layer:
            break
        for node, cost in layer.items():
            if best[node] is UNREACHED or cost < best[node]:
                best[node] = cost
        frontier = layer
    return {node: best[node] for node in graph.nodes()}


def oracle_negative(graph: Graph, source: int) -> bool:
    """True when a walk out of the source keeps shrinking past the ceiling.

    Relaxation reruns, no cleverness: one round past |V|, and any
    total still improving names a cycle pulling the walk down.
    Slow, complete, and the answer negative_cycle must match.
    """
    if not graph.has_node(source):
        raise GraphError(f"{source!r} is not a node, so no walk starts there")
    distances: dict = {source: 0}
    for _ in range(max(len(graph), 1) + 1):
        changed = False
        for node, target, weight in graph.edges():
            if node in distances:
                step = distances[node] + weight
                if target not in distances or step < distances[target]:
                    distances[target] = step
                    changed = True
        if not changed:
            return False
    return True

"""The cycle answer: a walk that answers None or one named cycle.

The walker's rounds stop at |V|-1 because a shortest walk needs no
more. When one more round still improves a total, a reachable cycle
is pulling the walk down forever - and this module names it honestly
instead of answering a distance no walk can finish with.

negative_cycle(graph, source) answers None when every walk settles,
or the cycle's nodes when one keeps shrinking. The naming walks the
predecessor chain back from a node the extra round moved: |V| hops
land inside the cycle, and the chain cannot escape it.
"""

from __future__ import annotations

from .graph import UNREACHED, Graph, GraphError


def negative_cycle(graph: Graph, source: int):
    """None if every walk settles; the cycle's nodes if one stays open.

    |V| rounds of relaxation with a parent chain; the first node the
    extra round still moves sits at the end of a chain that passes
    through a negative cycle. Walking parents back from there names
    the cycle - honest, because a settled graph moves nobody.
    """
    if not graph.has_node(source):
        raise GraphError(f"{source!r} is not a node, so no walk starts there")
    rounds = max(len(graph), 1)
    answer: dict = dict.fromkeys(graph.nodes(), UNREACHED)
    answer[source] = 0
    parent: dict = {}
    moved = None
    for round_index in range(rounds + 1):
        changed = False
        moved = None
        for node, target, weight in graph.edges():
            if answer[node] is not UNREACHED:
                step = answer[node] + weight
                if answer[target] is UNREACHED or step < answer[target]:
                    answer[target] = step
                    parent[target] = node
                    changed = True
                    if round_index == rounds:
                        moved = target
        if not changed:
            return None
    walker = moved
    for _ in range(rounds):
        if walker not in parent:
            return None
        walker = parent[walker]
    if walker not in parent:
        return None
    cycle = [walker]
    current = parent[walker]
    while current != walker:
        if current not in parent:
            return None
        cycle.append(current)
        current = parent[current]
    return tuple(sorted(cycle))

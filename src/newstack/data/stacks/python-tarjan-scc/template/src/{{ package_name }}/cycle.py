"""The cycle checker: a walk that answers None or one cycle.

The condensed graph owes every caller one promise - it is acyclic
- and this walker is how the promise is kept in the open: depth
first over an explicit stack, a node is open while its subtree is
under way, and a step onto an open node names the cycle it closed.
None means the walk finished with every node closed.
"""

from __future__ import annotations

from .graph import Graph

OPEN = 1
CLOSED = 2


def has_cycle(graph: Graph):
    """None if every walk closes; the cycle's nodes if one stays open."""
    state: dict = {}
    trail: list = []
    for start in graph.nodes():
        if state.get(start):
            continue
        state[start] = OPEN
        trail.append(start)
        work = [(start, iter(graph.successors(start)))]
        while work:
            node, children = work[-1]
            stepped = False
            for child in children:
                mark = state.get(child, 0)
                if mark == 0:
                    state[child] = OPEN
                    trail.append(child)
                    work.append((child, iter(graph.successors(child))))
                    stepped = True
                    break
                if mark == OPEN:
                    cut = len(trail) - 1
                    while trail[cut] != child:
                        cut -= 1
                    return tuple(trail[cut:])
            if not stepped:
                state[node] = CLOSED
                trail.pop()
                work.pop()
    return None

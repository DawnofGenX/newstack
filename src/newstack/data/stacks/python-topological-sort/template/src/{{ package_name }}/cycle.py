"""The tangle named, in order: deterministic DFS over sorted doors.

cycle(graph) answers the block honestly: None when nothing tangles
the graph, the smallest-label cycle otherwise. The walk starts at
the smallest label and takes doors in label order, so the same
tangle is named the same way in every run. The named cycle is the
answer order() refuses around.
"""

from __future__ import annotations

from .graph import Graph


def cycle(graph: Graph) -> tuple | None:
    """The first cycle the sorted walk meets, or None when none tangles.

    Depth-first from every label in order, doors in label order: the
    first node on the path the walk lands on twice opens the named
    cycle. Answering None is the honest answer for a graph that
    orders; answering the run of labels is the honest answer when a
    cycle blocks - the block named, never a shuffled list.
    """
    state: dict = {}
    path: list = []
    for start in graph.nodes():
        if state.get(start):
            continue
        state[start] = 1
        path.append(start)
        stack: list = [(start, iter(graph.successors(start)))]
        while stack:
            node, doors = stack[-1]
            for door in doors:
                mark = state.get(door)
                if mark == 1:
                    return tuple(path[path.index(door):])
                if mark:
                    continue
                state[door] = 1
                path.append(door)
                stack.append((door, iter(graph.successors(door))))
                break
            else:
                state[node] = 2
                path.pop()
                stack.pop()
    return None

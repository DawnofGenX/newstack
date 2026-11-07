"""The oracle: the dumb closure that never misses, only crawls slow.

The partition this library sells is the one this oracle answers:
two nodes share a component only when each reaches the other. The
closure walks every node's reach by hand - O(n^2) over the
transitive closure, honest and slow - and the fast walker in
scc.py must agree with it on every graph, shipped or seeded.

The oracle is the product. The walker is the way to afford it.
"""

from __future__ import annotations

from .graph import Graph


def reach(graph: Graph) -> dict:
    """node -> the frozen set of nodes it can reach, itself included."""
    answer = {}
    for start in graph.nodes():
        seen = {start}
        queue = [start]
        while queue:
            current = queue.pop()
            for nxt in graph.successors(current):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        answer[start] = frozenset(seen)
    return answer


def oracle_partition(graph: Graph) -> tuple:
    """The component partition, answered by mutual reachability alone.

    Two nodes share a component only when each reaches the other;
    everything else is an optimisation. Components are frozensets,
    ordered by their smallest label.
    """
    known = reach(graph)
    nodes = graph.nodes()
    groups: list = []
    claimed: set = set()
    for node in nodes:
        if node in claimed:
            continue
        partners = frozenset(
            other for other in nodes if node in known[other] and other in known[node]
        )
        claimed |= partners
        groups.append(partners)
    return tuple(sorted(groups, key=min))

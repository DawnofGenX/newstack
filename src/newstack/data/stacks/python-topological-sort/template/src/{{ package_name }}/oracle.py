"""The oracle: the naive picker that never hurries, only rescans.

The order this library sells is the one this oracle answers: from the
nodes still standing, pick the least whose predecessors have all
gone, drop it, rescan from the top. No frontier carried forward, no
cleverness - repeated pick-the-least-ready-node, the dumbest rule
that still lists a DAG.

order() in order.py must answer the same sequence node for node, on
every graph the corpora hold. On a tangled graph the picker stalls
with nodes standing and says so.
"""

from __future__ import annotations

from .graph import Graph


def naive_order(graph: Graph) -> tuple:
    """The order, answered slow: the least ready node, over and over."""
    standing = set(graph.nodes())
    listed: list = []
    while standing:
        chosen = None
        for node in sorted(standing):
            if not (set(graph.predecessors(node)) & standing):
                chosen = node
                break
        if chosen is None:
            raise ValueError(f"the picker stalled: {sorted(standing)} stay tangled")
        standing.discard(chosen)
        listed.append(chosen)
    return tuple(listed)

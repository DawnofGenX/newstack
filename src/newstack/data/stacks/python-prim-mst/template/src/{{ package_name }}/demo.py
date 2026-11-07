"""Six stories about spanning trees, every number computed live.

A story states a promise the grower owes the enumeration oracle
and answers it against the real modules - no hand-written
expectations, no stored figures. If any story stops holding, the
tool is wrong and says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import is_connected, synthetic
from .graph import Graph
from .oracle import min_cost
from .solve import audit, spanning_tree, tree_cost


@dataclass(frozen=True)
class Story:
    """One promise and the numbers that keep it."""

    title: str
    detail: str
    held: bool


def _lattice() -> Graph:
    graph = Graph()
    for low, high, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(low, high, weight)
    return graph


def stories() -> list:
    """The six stories, told against the live modules."""
    lattice = _lattice()
    grown = spanning_tree(lattice, 1)
    least = min_cost(lattice)
    first = Story(
        "the grower answers the enumeration's minimum, total for total",
        f"grown={tree_cost(lattice, 1)} oracle={least} equal={tree_cost(lattice, 1) == least}",
        tree_cost(lattice, 1) == least,
    )

    shapes = audit(lattice, 1, grown)
    second = Story(
        "the tree is a tree: |V|-1 edges, every node touched once",
        f"edges={len(grown)} nodes={len(lattice)} breaks={shapes}",
        shapes == [] and len(grown) == len(lattice) - 1,
    )

    ties = Graph()
    for low, high, weight in ((1, 2, 1), (2, 3, 1), (1, 3, 1), (3, 4, 2)):
        ties.add_edge(low, high, weight)
    drawn = spanning_tree(ties, 1)
    repeated = spanning_tree(ties, 1)
    third = Story(
        "equal weights pick the same tree, run after run",
        f"tree={sorted(drawn)} stable={drawn == repeated}",
        drawn == repeated and len(drawn) == 3,
    )

    corpus = synthetic(20, seed=11)
    drifted = sum(
        1 for graph in corpus if tree_cost(graph, min(graph.nodes())) != min_cost(graph)
    )
    fourth = Story(
        "a seeded corpus answers the enumeration's minimum, graph after graph",
        f"graphs={len(corpus)} drifted={drifted}",
        drifted == 0,
    )

    chain = Graph()
    for step in range(8):
        chain.add_edge(step, step + 1, step + 1)
    walked = tree_cost(chain, 0)
    fifth = Story(
        "a chain's tree is the chain: every door is the only door",
        f"nodes={len(chain)} cost={walked} least={min_cost(chain)}",
        walked == min_cost(chain) == sum(range(1, 9)),
    )

    apart = Graph()
    for low, high, weight in ((1, 2, 3), (7, 8, 1)):
        apart.add_edge(low, high, weight)
    sixth = Story(
        "a graph in pieces is named, never spanned",
        f"connected={is_connected(apart)} nodes={len(apart)}",
        not is_connected(apart),
    )
    return [first, second, third, fourth, fifth, sixth]

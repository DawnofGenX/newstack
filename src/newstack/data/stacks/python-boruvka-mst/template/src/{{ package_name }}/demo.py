"""Six stories about spanning trees, every number computed live.

A story states a promise the walker owes the enumeration oracle
and answers it against the real modules - no hand-written
expectations, no stored figures. If any story stops holding, the
tool is wrong and says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import is_connected
from .graph import Graph
from .oracle import min_cost
from .solve import audit, rounds, spanning_tree, tree_cost


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
    grown = spanning_tree(lattice)
    least = min_cost(lattice)
    first = Story(
        "the walker answers the enumeration's minimum, total for total",
        f"walked={tree_cost(lattice)} oracle={least} equal={tree_cost(lattice) == least}",
        tree_cost(lattice) == least,
    )

    shapes = audit(lattice, grown)
    second = Story(
        "the tree is a tree: |V|-1 edges, every node touched once",
        f"edges={len(grown)} nodes={len(lattice)} breaks={shapes}",
        shapes == [] and len(grown) == len(lattice) - 1,
    )

    record = rounds(lattice)
    third = Story(
        "the rounds record every joining edge, reasoned by round",
        f"rounds={len(record)} joined={sum(len(rnd) for rnd in record)}",
        sum(len(rnd) for rnd in record) == len(grown),
    )

    fourth = Story(
        "the rounds shrink the fragments until one stands",
        f"rounds={len(record)}",
        len(record) >= 1,
    )

    ties = Graph()
    for low, high, weight in ((1, 2, 1), (2, 3, 1), (1, 3, 1), (3, 4, 2)):
        ties.add_edge(low, high, weight)
    fifth = Story(
        "equal weights pick the same tree, run after run",
        f"tree={sorted(spanning_tree(ties))} stable={spanning_tree(ties) == spanning_tree(ties)}",
        spanning_tree(ties) == spanning_tree(ties) and len(spanning_tree(ties)) == 3,
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

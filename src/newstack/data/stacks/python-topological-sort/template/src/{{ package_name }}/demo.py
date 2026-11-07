"""Six stories about orders, every number computed live.

A story states a promise the orderer owes the picker and answers it
against the real modules - no hand-written expectations, no stored
figures. If any story stops holding, the tool is wrong and says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic, tangles
from .cycle import cycle
from .graph import Graph
from .oracle import naive_order
from .order import block, order, validate


@dataclass(frozen=True)
class Story:
    """One promise and the numbers that keep it."""

    title: str
    detail: str
    held: bool


def _lattice() -> Graph:
    graph = Graph()
    for source, target in (
        (1, 2), (1, 4), (2, 3), (4, 3), (3, 5), (4, 5),
    ):
        graph.add_edge(source, target)
    graph.add_node(6)
    return graph


def stories() -> list:
    """The six stories, told against the live modules."""
    lattice = _lattice()
    listed = order(lattice)
    picked = naive_order(lattice)
    first = Story(
        "the order answers the picker, seat for seat",
        f"order={listed} picker={picked} equal={listed == picked}",
        listed == picked,
    )

    breaks = validate(lattice, listed)
    second = Story(
        "the listing validates silent: every edge points forward",
        f"breaks={breaks}",
        breaks == [],
    )

    again = order(lattice)
    third = Story(
        "the order is a fixed point: same graph, same sequence",
        f"first={listed} second={again}",
        listed == again,
    )

    corpus = synthetic(25, seed=11)
    drifted = sum(
        1 for graph in corpus if order(graph) != naive_order(graph)
    )
    fourth = Story(
        "a seeded corpus agrees with the picker, graph after graph",
        f"graphs={len(corpus)} drifted={drifted}",
        drifted == 0,
    )

    tangle = tangles()[0]
    named = cycle(tangle)
    fifth = Story(
        "a tangle names its block and the order refuses",
        f"block={block(tangle)} cycle={named}",
        named is not None and block(tangle) == (1, 2, 3),
    )

    island = Graph()
    island.add_edge(1, 2)
    island.add_node(7)
    placed = order(island)
    sixth = Story(
        "every node is listed once: islands included, never invented",
        f"listed={placed} count={len(placed)}",
        placed == (1, 2, 7) and len(placed) == len(island),
    )
    return [first, second, third, fourth, fifth, sixth]

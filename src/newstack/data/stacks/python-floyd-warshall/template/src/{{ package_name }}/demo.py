"""Six stories about distance tables, every number computed live.

A story states a promise the matrix owes the walking oracle and
answers it against the real modules - no hand-written expectations,
no stored figures. If any story stops holding, the tool is wrong
and says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic
from .graph import Graph
from .oracle import distance_table
from .solve import distances, restated, worst_hop


@dataclass(frozen=True)
class Story:
    """One promise and the numbers that keep it."""

    title: str
    detail: str
    held: bool


def _lattice() -> Graph:
    graph = Graph()
    for source, target, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(source, target, weight)
    return graph


def stories() -> list:
    """The six stories, told against the live modules."""
    lattice = _lattice()
    answered = distances(lattice)
    walked = distance_table(lattice)
    first = Story(
        "the table answers the walker, pair for pair",
        f"table={len(answered)} walker={len(walked)} equal={answered == walked}",
        answered == walked,
    )

    resting = restated(answered)
    second = Story(
        "one more sweep changes nothing: the table rests where it sits",
        f"pairs={len(answered)} rest={resting == answered}",
        resting == answered,
    )

    chain = Graph()
    for step in range(8):
        chain.add_edge(step, step + 1, step + 1)
    walked_chain = distances(chain)
    farthest = worst_hop(chain)
    third = Story(
        "a chain\'s table walks end to end and never back",
        f"pairs={len(walked_chain)} far={farthest} back={(8, 0) in walked_chain}",
        len(walked_chain) == 9 * 10 // 2 and farthest == (0, 8, 36) and (8, 0) not in walked_chain,
    )

    corpus = synthetic(20, seed=11)
    drifted = sum(1 for graph in corpus if distances(graph) != distance_table(graph))
    fourth = Story(
        "a seeded corpus answers the walker, graph after graph",
        f"graphs={len(corpus)} drifted={drifted}",
        drifted == 0,
    )

    one_way = Graph().add_edge(1, 2, 3)
    apart = distances(one_way)
    fifth = Story(
        "an arrow points: forward is walked, backward is omitted",
        f"table={apart} forwards={(1, 2) in apart} backwards={(2, 1) in apart}",
        apart == {(1, 1): 0, (1, 2): 3, (2, 2): 0} and (2, 1) not in apart,
    )

    lone = Graph()
    lone.add_node(7)
    still = distances(lone)
    sixth = Story(
        "a lone node stands at zero on itself and is distant from nothing",
        f"table={still} nodes={len(lone)}",
        still == {(7, 7): 0},
    )
    return [first, second, third, fourth, fifth, sixth]

"""Six stories about weighted walks, every number computed live.

A story states a promise the walker owes the oracle and answers it
against the real modules - no hand-written expectations, no stored
figures. If any story stops holding, the tool is wrong and says so.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic
from .cycle import negative_cycle
from .graph import Graph
from .oracle import oracle_distances, oracle_negative
from .walk import audit, distances, settled


@dataclass(frozen=True)
class Story:
    """One promise and the numbers that keep it."""

    title: str
    detail: str
    held: bool


def _diamond() -> Graph:
    graph = Graph()
    for source, target, weight in (
        (1, 2, 4),
        (2, 3, -2),
        (3, 4, 3),
        (1, 3, 5),
        (2, 4, 1),
    ):
        graph.add_edge(source, target, weight)
    return graph


def _cycled() -> Graph:
    graph = Graph()
    for source, target, weight in ((0, 1, -2), (1, 2, 1), (2, 0, 0), (2, 3, 4)):
        graph.add_edge(source, target, weight)
    return graph


def stories() -> list:
    """The six stories, told against the live modules."""
    diamond = _diamond()
    walked = distances(diamond, 1)
    counted = oracle_distances(diamond, 1)
    first = Story(
        "the walker answers the oracle, node for node",
        f"walked={walked} counted={counted} equal={walked == counted}",
        walked == counted,
    )

    second = Story(
        "a negative weight walks where the direct edge would not",
        f"one_to_three={walked[3]} direct=5 cheaper={walked[3] < 5}",
        walked[3] == 2 and walked[4] == 5,
    )

    chain = Graph()
    for step in range(9):
        chain.add_edge(step, step + 1, -2 - step)
    tail = distances(chain, 0)[9]
    third = Story(
        "a chain settles: |V|-1 rounds, one honest total",
        f"cost={tail} sum=-54 equal={tail == -54}",
        tail == -54 and not settled(chain, 0),
    )

    corpus = synthetic(25, seed=11)
    drifted = sum(
        1 for graph in corpus if distances(graph, graph.nodes()[0])
        != oracle_distances(graph, graph.nodes()[0])
    )
    fourth = Story(
        "a seeded corpus agrees with the count, graph after graph",
        f"graphs={len(corpus)} drifted={drifted}",
        drifted == 0,
    )

    quiet = sum(1 for graph in corpus if not settled(graph, graph.nodes()[0]))
    fifth = Story(
        "no shipped graph still relaxes an edge once walked",
        f"graphs={len(corpus)} loose={quiet} shape={audit(diamond, 1, walked) == []}",
        quiet == len(corpus) and audit(diamond, 1, walked) == [],
    )

    cycled = _cycled()
    named = negative_cycle(cycled, 0)
    sixth = Story(
        "a negative cycle is named, not answered past",
        f"cycle={list(named) if named else None} "
        f"oracle={oracle_negative(cycled, 0)}",
        named is not None and oracle_negative(cycled, 0)
        and named == (0, 1, 2),
    )
    return [first, second, third, fourth, fifth, sixth]

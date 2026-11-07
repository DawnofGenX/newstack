from __future__ import annotations

from {{ package_name }}.cycle import (
    negative_cycle,
)
from {{ package_name }}.graph import (
    Graph,
    GraphError,
)


def cycled() -> Graph:
    graph = Graph()
    for source, target, weight in ((0, 1, -2), (1, 2, 1), (2, 0, 0), (2, 3, 4)):
        graph.add_edge(source, target, weight)
    return graph


def diamond() -> Graph:
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


def test_a_negative_cycle_is_named() -> None:
    assert negative_cycle(cycled(), 0) == (0, 1, 2)


def test_the_named_cycle_carries_a_negative_total() -> None:
    graph = cycled()
    total = sum(graph.weight(a, b) for a, b in ((0, 1), (1, 2), (2, 0)))
    assert total < 0


def test_a_settling_graph_names_no_cycle() -> None:
    assert negative_cycle(diamond(), 1) is None
    chain = Graph()
    for step in range(9):
        chain.add_edge(step, step + 1, -2 - step)
    assert negative_cycle(chain, 0) is None


def test_a_positive_ring_answers_none() -> None:
    ring = Graph()
    for step in range(6):
        ring.add_edge(step, (step + 1) % 6, 2)
    assert negative_cycle(ring, 0) is None


def test_a_cycle_far_from_the_source_is_none() -> None:
    graph = Graph()
    for source, target, weight in ((0, 1, 5), (2, 3, -2), (3, 2, 0)):
        graph.add_edge(source, target, weight)
    assert negative_cycle(graph, 0) is None


def test_a_stranger_names_no_walk() -> None:
    try:
        negative_cycle(diamond(), 99)
    except GraphError:
        return
    raise AssertionError("a stranger walked")


def test_a_deep_cycle_is_named_not_missed() -> None:
    graph = Graph()
    for step in range(7):
        graph.add_edge(step, step + 1, 1)
    graph.add_edge(7, 5, -9)
    assert negative_cycle(graph, 0) == (5, 6, 7)

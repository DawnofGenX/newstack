from __future__ import annotations

from {{ package_name }}.graph import (
    UNREACHED,
    Graph,
    GraphError,
)
from {{ package_name }}.oracle import (
    oracle_distances,
    oracle_negative,
)


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


def cycled() -> Graph:
    graph = Graph()
    for source, target, weight in ((0, 1, -2), (1, 2, 1), (2, 0, 0), (2, 3, 4)):
        graph.add_edge(source, target, weight)
    return graph


def test_the_count_answers_exact_totals() -> None:
    assert oracle_distances(diamond(), 1) == {1: 0, 2: 4, 3: 2, 4: 5}


def test_the_count_names_the_source_zero() -> None:
    assert oracle_distances(diamond(), 1)[1] == 0


def test_the_count_answers_unreachable_honestly() -> None:
    graph = Graph()
    graph.add_node(3).add_node(8)
    assert oracle_distances(graph, 3) == {3: 0, 8: UNREACHED}


def test_the_count_seats_every_node_once() -> None:
    answer = oracle_distances(diamond(), 1)
    assert sorted(answer) == sorted(diamond().nodes())


def test_a_stranger_names_no_walk() -> None:
    try:
        oracle_distances(diamond(), 99)
    except GraphError:
        return
    raise AssertionError("a stranger counted")


def test_a_settling_graph_pulls_nothing_down() -> None:
    assert not oracle_negative(diamond(), 1)
    chain = Graph()
    for step in range(9):
        chain.add_edge(step, step + 1, -2 - step)
    assert not oracle_negative(chain, 0)


def test_a_negative_cycle_keeps_the_count_shrinking() -> None:
    assert oracle_negative(cycled(), 0)


def test_a_positive_ring_is_honest_quiet() -> None:
    ring = Graph()
    for step in range(6):
        ring.add_edge(step, (step + 1) % 6, 2)
    assert not oracle_negative(ring, 0)


def test_the_count_needs_its_full_depth() -> None:
    chain = Graph()
    for step in range(12):
        chain.add_edge(step, step + 1, -1)
    assert oracle_distances(chain, 0)[12] == -12

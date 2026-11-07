from __future__ import annotations

from {{ package_name }}.graph import (
    UNREACHED,
    Graph,
    GraphError,
)
from {{ package_name }}.walk import (
    audit,
    distances,
    settled,
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


def test_the_walk_answers_exact_totals() -> None:
    assert distances(diamond(), 1) == {1: 0, 2: 4, 3: 2, 4: 5}


def test_the_source_answers_zero() -> None:
    assert distances(diamond(), 1)[1] == 0


def test_a_chain_walks_its_whole_length() -> None:
    graph = Graph()
    for step in range(9):
        graph.add_edge(step, step + 1, -2 - step)
    assert distances(graph, 0)[9] == -54


def test_a_long_chain_needs_its_rounds() -> None:
    graph = Graph()
    for step in range(20):
        graph.add_edge(step, step + 1, -1)
    assert distances(graph, 0)[20] == -20


def test_an_unreachable_node_answers_honestly() -> None:
    graph = Graph()
    graph.add_node(3).add_node(8)
    assert distances(graph, 3) == {3: 0, 8: UNREACHED}


def test_a_stranger_names_no_walk() -> None:
    try:
        distances(diamond(), 99)
    except GraphError:
        return
    raise AssertionError("a stranger walked")


def test_no_edge_survives_settled() -> None:
    assert settled(diamond(), 1) == []
    graph = Graph()
    for step in range(9):
        graph.add_edge(step, step + 1, -2 - step)
    assert settled(graph, 0) == []


def test_the_audit_names_shape_breaks() -> None:
    graph = diamond()
    assert audit(graph, 1, distances(graph, 1)) == []
    assert audit(graph, 1, {1: 0, 2: 4}) != []

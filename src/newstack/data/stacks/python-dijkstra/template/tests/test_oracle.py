from __future__ import annotations

from {{ package_name }}.graph import (
    Graph,
)
from {{ package_name }}.oracle import (
    oracle_distances,
    relax_map,
)


def lattice() -> Graph:
    graph = Graph()
    for source, target, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(source, target, weight)
    graph.add_node(6)
    return graph


def test_the_source_sits_at_zero() -> None:
    assert relax_map(lattice(), 1)[1] == 0


def test_the_fixed_point_prefers_the_cheap_lane() -> None:
    costs = relax_map(lattice(), 1)
    assert costs[3] == 3
    assert costs[5] == 6


def test_an_island_keeps_no_key() -> None:
    assert 6 not in relax_map(lattice(), 1)


def test_the_published_face_answers_the_same_map() -> None:
    assert oracle_distances(lattice(), 1) == relax_map(lattice(), 1)


def test_a_stranger_sources_nothing() -> None:
    try:
        relax_map(lattice(), 99)
    except KeyError:
        return
    raise AssertionError("a stranger answered a map")


def test_a_zero_weight_hop_is_crossed_free() -> None:
    graph = Graph()
    graph.add_edge(1, 2, 0)
    graph.add_edge(2, 3, 0)
    assert relax_map(graph, 1) == {1: 0, 2: 0, 3: 0}


def test_a_ring_relaxes_to_rest() -> None:
    graph = Graph()
    for step in range(5):
        graph.add_edge(step, (step + 1) % 5, 1)
    assert relax_map(graph, 0) == {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}

from __future__ import annotations

from {{ package_name }}.corpus import (
    synthetic,
)
from {{ package_name }}.graph import (
    Graph,
)
from {{ package_name }}.oracle import (
    distance_table,
)
from {{ package_name }}.solve import (
    TableError,
    audit,
    distances,
    restated,
    worst_hop,
)


def lattice() -> Graph:
    graph = Graph()
    for source, target, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(source, target, weight)
    return graph


def test_the_matrix_answers_the_walker_on_the_lattice() -> None:
    assert distances(lattice()) == distance_table(lattice())


def test_the_diagonal_sits_at_zero() -> None:
    table = distances(lattice())
    for node in lattice().nodes():
        assert table[(node, node)] == 0


def test_the_audit_stays_silent() -> None:
    assert audit(lattice(), distances(lattice())) == []


def test_one_more_sweep_moves_nothing() -> None:
    assert restated(distances(lattice())) == distances(lattice())


def test_the_worst_hop_is_the_farthest_road() -> None:
    assert worst_hop(lattice()) == (1, 5, 6)


def test_an_unreached_pair_is_omitted_not_infinite() -> None:
    table = distances(lattice())
    assert (5, 1) not in table
    assert all(cost < float("inf") for cost in table.values())


def test_a_chain_walks_end_to_end_and_never_back() -> None:
    chain = Graph()
    for step in range(8):
        chain.add_edge(step, step + 1, step + 1)
    table = distances(chain)
    assert table[(0, 8)] == 36
    assert (8, 0) not in table
    assert worst_hop(chain) == (0, 8, 36)


def test_a_lone_node_distances_nothing() -> None:
    lone = Graph()
    lone.add_node(7)
    assert distances(lone) == {(7, 7): 0}
    try:
        worst_hop(lone)
    except TableError:
        pass
    else:
        raise AssertionError("a lone node named a distance")


def test_a_seeded_corpus_answers_the_walker_graph_after_graph() -> None:
    for graph in synthetic(25, seed=7):
        answered = distances(graph)
        assert answered == distance_table(graph)
        assert audit(graph, answered) == []
        assert restated(answered) == answered

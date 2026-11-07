from __future__ import annotations

from {{ package_name }}.graph import (
    Graph,
)
from {{ package_name }}.oracle import (
    OracleError,
    min_cost,
    oracle_cost,
    spanning_trees,
    tree_total,
)


def lattice() -> Graph:
    graph = Graph()
    for low, high, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(low, high, weight)
    return graph


def test_the_enumeration_draws_every_spanning_tree() -> None:
    trees = spanning_trees(lattice())
    assert len(trees) >= 1
    for tree in trees:
        assert len(tree) == len(lattice()) - 1


def test_the_enumeration_least_is_the_lowest_drawn_total() -> None:
    trees = spanning_trees(lattice())
    assert min_cost(lattice()) == min(tree_total(tree) for tree in trees)


def test_the_oracle_answers_the_enumerations_least() -> None:
    assert oracle_cost(lattice()) == min_cost(lattice())


def test_a_pair_draws_exactly_one_tree() -> None:
    graph = Graph().add_edge(1, 2, 5)
    assert spanning_trees(graph) == [frozenset({((1, 2), 5)})]
    assert min_cost(graph) == 5


def test_a_lone_node_spans_empty() -> None:
    lone = Graph().add_node(4)
    assert spanning_trees(lone) == [frozenset()]
    assert min_cost(lone) == 0


def test_a_graph_in_pieces_draws_nothing() -> None:
    apart = Graph().add_edge(1, 2, 1).add_node(9)
    try:
        spanning_trees(apart)
    except OracleError:
        pass
    else:
        raise AssertionError("a graph in pieces drew a tree")
    try:
        min_cost(apart)
    except OracleError:
        pass
    else:
        raise AssertionError("a graph in pieces named a minimum")


def test_a_drawn_set_totals_its_weights() -> None:
    drawn = frozenset({((1, 2), 4), ((2, 3), 1)})
    assert tree_total(drawn) == 5

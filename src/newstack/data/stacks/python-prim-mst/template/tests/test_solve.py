from __future__ import annotations

from {{ package_name }}.corpus import (
    synthetic,
)
from {{ package_name }}.graph import (
    Graph,
)
from {{ package_name }}.oracle import (
    min_cost,
)
from {{ package_name }}.solve import (
    TreeError,
    audit,
    spanning_tree,
    tree_cost,
)


def lattice() -> Graph:
    graph = Graph()
    for low, high, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(low, high, weight)
    return graph


def test_the_grower_answers_the_enumeration_on_the_lattice() -> None:
    assert tree_cost(lattice(), 1) == min_cost(lattice())


def test_the_tree_is_a_tree() -> None:
    grown = spanning_tree(lattice(), 1)
    assert len(grown) == len(lattice()) - 1
    assert audit(lattice(), 1, grown) == []


def test_the_grower_is_the_same_answer_twice() -> None:
    assert spanning_tree(lattice(), 1) == spanning_tree(lattice(), 1)


def test_equal_weights_pick_the_same_tree() -> None:
    ties = Graph()
    for low, high, weight in ((1, 2, 1), (2, 3, 1), (1, 3, 1), (3, 4, 2)):
        ties.add_edge(low, high, weight)
    grown = spanning_tree(ties, 1)
    assert grown == frozenset({((1, 2), 1), ((1, 3), 1), ((3, 4), 2)})
    assert tree_cost(ties, 1) == min_cost(ties)


def test_the_total_is_start_independent() -> None:
    assert tree_cost(lattice(), 1) == tree_cost(lattice(), 5)


def test_a_chain_spans_every_door() -> None:
    chain = Graph()
    for step in range(8):
        chain.add_edge(step, step + 1, step + 1)
    assert tree_cost(chain, 0) == sum(range(1, 9))
    assert len(spanning_tree(chain, 0)) == 8


def test_a_lone_node_spans_empty() -> None:
    assert spanning_tree(Graph().add_node(4), 4) == frozenset()
    assert tree_cost(Graph().add_node(4), 4) == 0


def test_a_graph_in_pieces_is_named_not_spanned() -> None:
    apart = Graph().add_edge(1, 2, 3).add_edge(7, 8, 1)
    try:
        spanning_tree(apart, 1)
    except TreeError:
        pass
    else:
        raise AssertionError("a graph in pieces grew a tree")


def test_a_stranger_starts_nothing() -> None:
    try:
        spanning_tree(lattice(), 99)
    except KeyError:
        pass
    else:
        raise AssertionError("a stranger grew a tree")


def test_a_seeded_corpus_answers_the_enumeration_graph_after_graph() -> None:
    for graph in synthetic(25, seed=7):
        start = min(graph.nodes())
        grown = spanning_tree(graph, start)
        assert tree_cost(graph, start) == min_cost(graph)
        assert len(grown) == len(graph) - 1
        assert audit(graph, start, grown) == []

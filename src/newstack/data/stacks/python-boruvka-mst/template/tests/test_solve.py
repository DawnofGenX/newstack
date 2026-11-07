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
    Fragment,
    TreeError,
    audit,
    rounds,
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


def test_the_walker_answers_the_enumeration_on_the_lattice() -> None:
    assert tree_cost(lattice()) == min_cost(lattice())


def test_the_tree_is_a_tree() -> None:
    grown = spanning_tree(lattice())
    assert len(grown) == len(lattice()) - 1
    assert audit(lattice(), grown) == []


def test_the_walker_is_the_same_answer_twice() -> None:
    assert spanning_tree(lattice()) == spanning_tree(lattice())


def test_the_rounds_join_every_fragment() -> None:
    record = rounds(lattice())
    assert len(record) >= 1
    taken = {edge for rnd in record for edge in rnd}
    assert taken == spanning_tree(lattice())
    assert all(len(rnd) >= 1 for rnd in record)


def test_the_rounds_cover_the_triangle() -> None:
    triangle = Graph().add_edge(1, 2, 4).add_edge(2, 3, 1).add_edge(1, 3, 1)
    record = rounds(triangle)
    taken = {edge for rnd in record for edge in rnd}
    assert len(taken) == 2
    assert taken == spanning_tree(triangle)


def test_equal_weights_pick_the_same_tree() -> None:
    ties = Graph()
    for low, high, weight in ((1, 2, 1), (2, 3, 1), (1, 3, 1), (3, 4, 2)):
        ties.add_edge(low, high, weight)
    grown = spanning_tree(ties)
    assert grown == frozenset({((1, 2), 1), ((1, 3), 1), ((3, 4), 2)})
    assert tree_cost(ties) == min_cost(ties)


def test_a_chain_spans_every_door() -> None:
    chain = Graph()
    for step in range(8):
        chain.add_edge(step, step + 1, step + 1)
    assert tree_cost(chain) == sum(range(1, 9))
    assert len(spanning_tree(chain)) == 8


def test_a_lone_node_spans_empty() -> None:
    assert spanning_tree(Graph().add_node(4)) == frozenset()
    assert tree_cost(Graph().add_node(4)) == 0


def test_a_graph_in_pieces_is_named_not_walked() -> None:
    apart = Graph().add_edge(1, 2, 3).add_edge(7, 8, 1)
    try:
        spanning_tree(apart)
    except TreeError:
        pass
    else:
        raise AssertionError("a graph in pieces walked a tree")


def test_the_fragments_join_never_split() -> None:
    fragments = Fragment((1, 2, 3))
    assert fragments.find(2) == 2
    fragments.join(3, 1)
    assert fragments.find(3) == fragments.find(1)
    assert fragments.find(2) != fragments.find(3)
    fragments.join(2, 3)
    assert fragments.one_piece()


def test_a_seeded_corpus_answers_the_enumeration_graph_after_graph() -> None:
    for graph in synthetic(25, seed=7):
        grown = spanning_tree(graph)
        assert tree_cost(graph) == min_cost(graph)
        assert len(grown) == len(graph) - 1
        assert audit(graph, grown) == []
        taken = {edge for rnd in rounds(graph) for edge in rnd}
        assert taken == grown

from __future__ import annotations

from {{ package_name }}.corpus import (
    synthetic,
)
from {{ package_name }}.cycle import (
    has_cycle,
)
from {{ package_name }}.graph import (
    Graph,
)
from {{ package_name }}.scc import (
    condense,
)


def test_a_chain_clears_the_walk() -> None:
    graph = Graph()
    for step in range(6):
        graph.add_edge(step, step + 1)
    assert has_cycle(graph) is None


def test_a_ring_names_its_cycle() -> None:
    graph = Graph()
    for step in range(5):
        graph.add_edge(step, (step + 1) % 5)
    cycle = has_cycle(graph)
    assert cycle is not None
    assert set(cycle) == set(range(5))


def test_a_lone_node_clears_the_walk() -> None:
    assert has_cycle(Graph().add_node(3)) is None


def test_the_fold_clears_the_walk_on_every_graph() -> None:
    for graph in synthetic(50, seed=17):
        assert has_cycle(condense(graph)) is None


def test_the_checker_walks_branches_and_rejoins() -> None:
    graph = Graph()
    for source, target in ((1, 2), (1, 3), (2, 4), (3, 4), (4, 5)):
        graph.add_edge(source, target)
    assert has_cycle(graph) is None
    graph.add_edge(5, 2)
    cycle = has_cycle(graph)
    assert cycle is not None
    assert 2 in cycle and 5 in cycle


def test_a_repeated_edge_is_not_a_cycle() -> None:
    graph = Graph()
    graph.add_edge(1, 2)
    graph.add_edge(1, 2)
    assert has_cycle(graph) is None

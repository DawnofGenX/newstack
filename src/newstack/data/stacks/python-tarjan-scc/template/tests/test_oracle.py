from __future__ import annotations

from {{ package_name }}.graph import (
    Graph,
)
from {{ package_name }}.oracle import (
    oracle_partition,
    reach,
)


def diamond() -> Graph:
    graph = Graph()
    for source, target in ((1, 2), (2, 3), (3, 1), (3, 4), (4, 5), (5, 4), (4, 6)):
        graph.add_edge(source, target)
    return graph


def test_reach_includes_the_self() -> None:
    closed = reach(diamond())
    for node in diamond().nodes():
        assert node in closed[node]


def test_reach_follows_the_arrows() -> None:
    closed = reach(diamond())
    assert closed[1] == frozenset({1, 2, 3, 4, 5, 6})
    assert closed[6] == frozenset({6})


def test_the_oracle_splits_the_diamond() -> None:
    assert oracle_partition(diamond()) == (
        frozenset({1, 2, 3}),
        frozenset({4, 5}),
        frozenset({6}),
    )


def test_the_oracle_orders_components_by_head() -> None:
    heads = [min(group) for group in oracle_partition(diamond())]
    assert heads == sorted(heads)


def test_a_chain_splits_to_singletons() -> None:
    graph = Graph()
    for step in range(4):
        graph.add_edge(step, step + 1)
    groups = oracle_partition(graph)
    assert all(len(group) == 1 for group in groups)
    assert len(groups) == 5


def test_a_ring_walks_whole() -> None:
    graph = Graph()
    for step in range(6):
        graph.add_edge(step, (step + 1) % 6)
    assert oracle_partition(graph) == (frozenset(range(6)),)


def test_an_isolated_node_is_its_own_component() -> None:
    graph = Graph().add_node(9)
    assert oracle_partition(graph) == (frozenset({9}),)


def test_the_oracle_seats_every_node_once() -> None:
    groups = oracle_partition(diamond())
    seats = [member for group in groups for member in group]
    assert sorted(seats) == sorted(diamond().nodes())
    assert len(seats) == len(set(seats))

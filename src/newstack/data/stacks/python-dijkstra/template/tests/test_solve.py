from __future__ import annotations

from {{ package_name }}.corpus import (
    synthetic,
)
from {{ package_name }}.graph import (
    Graph,
)
from {{ package_name }}.oracle import (
    relax_map,
)
from {{ package_name }}.solve import (
    RouteError,
    audit,
    distances,
    path,
)


def lattice() -> Graph:
    graph = Graph()
    for source, target, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(source, target, weight)
    graph.add_node(6)
    return graph


def test_the_walker_answers_the_fixed_point_on_the_lattice() -> None:
    graph = lattice()
    assert distances(graph, 1) == relax_map(graph, 1)


def test_the_lattice_map_carries_the_cheap_lane() -> None:
    assert distances(lattice(), 1) == {1: 0, 2: 4, 3: 3, 4: 2, 5: 6}


def test_the_settled_pick_takes_the_cheapest_not_the_last() -> None:
    graph = Graph()
    for source, target, weight in ((1, 2, 9), (1, 3, 1), (3, 2, 1), (2, 4, 1), (3, 4, 8)):
        graph.add_edge(source, target, weight)
    assert distances(graph, 1)[4] == 3


def test_a_route_costs_the_maps_cost() -> None:
    graph = lattice()
    route, cost = path(graph, 1, 5)
    assert cost == distances(graph, 1)[5]
    assert route == (1, 4, 3, 5)


def test_a_self_route_is_itself_at_zero() -> None:
    assert path(lattice(), 1, 1) == ((1,), 0)


def test_a_stranger_target_is_refused() -> None:
    try:
        path(lattice(), 1, 99)
    except KeyError:
        return
    raise AssertionError("a stranger got a route")


def test_a_beyond_reach_target_is_refused() -> None:
    try:
        path(lattice(), 1, 6)
    except RouteError:
        return
    raise AssertionError("an island got a route")


def test_the_audit_walks_edges_and_stays_silent() -> None:
    graph = lattice()
    assert audit(graph, 1, distances(graph, 1)) == []


def test_a_doctored_map_is_named() -> None:
    graph = lattice()
    costs = distances(graph, 1)
    costs[5] = 99
    assert audit(graph, 1, costs)


def test_a_disconnected_pair_maps_only_its_own_end() -> None:
    graph = Graph()
    graph.add_edge(1, 2, 3)
    graph.add_edge(7, 8, 1)
    assert distances(graph, 1) == {1: 0, 2: 3}
    assert distances(graph, 7) == {7: 0, 8: 1}


def test_the_walker_matches_the_fixed_point_on_every_seeded_graph() -> None:
    for graph in synthetic(40, seed=17):
        source = min(graph.nodes())
        costs = distances(graph, source)
        assert costs == relax_map(graph, source)
        assert audit(graph, source, costs) == []
        for target in costs:
            assert path(graph, source, target)[1] == costs[target]


def test_a_chain_costs_the_whole_sum() -> None:
    chain = Graph()
    for step in range(9):
        chain.add_edge(step, step + 1, step + 1)
    assert distances(chain, 0)[9] == 45

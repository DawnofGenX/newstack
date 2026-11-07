from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    synthetic,
)
from {{ package_name }}.graph import (
    Graph,
)
from {{ package_name }}.oracle import (
    min_cut,
)
from {{ package_name }}.solve import (
    FlowError,
    audit,
    flow_map,
    max_flow,
)


def diamond() -> Graph:
    graph = Graph()
    for start, end, room in (
        (0, 1, 3), (1, 3, 2), (0, 2, 2), (2, 3, 3), (0, 3, 1), (1, 2, 1),
    ):
        graph.add_edge(start, end, room)
    return graph


def test_the_walker_answers_the_enumeration_on_the_diamond() -> None:
    assert max_flow(diamond(), 0, 3) == min_cut(diamond(), 0, 3) == 6


def test_the_map_ships_what_the_source_let_go() -> None:
    shipped = flow_map(diamond(), 0, 3)
    out = sum(amount for (start, _end), amount in shipped.items() if start == 0)
    assert out == max_flow(diamond(), 0, 3)


def test_the_map_conserves_at_every_interior_node() -> None:
    assert audit(diamond(), 0, 3, flow_map(diamond(), 0, 3)) == []


def test_the_walker_is_the_same_answer_twice() -> None:
    assert flow_map(diamond(), 0, 3) == flow_map(diamond(), 0, 3)


def test_a_chain_carries_its_least_door() -> None:
    chain = Graph()
    for step in range(8):
        chain.add_edge(step, step + 1, step + 1)
    assert max_flow(chain, 0, 8) == 1


def test_a_closed_door_carries_nothing() -> None:
    assert max_flow(Graph().add_edge(1, 2, 0), 1, 2) == 0


def test_no_route_carries_zero_not_a_refusal() -> None:
    apart = Graph().add_edge(1, 2, 4).add_node(8)
    assert max_flow(apart, 1, 8) == 0


def test_ends_that_match_walk_nothing() -> None:
    with pytest.raises(FlowError):
        max_flow(diamond(), 0, 0)


def test_a_stranger_is_no_source() -> None:
    with pytest.raises(KeyError):
        max_flow(diamond(), 99, 3)


def test_a_seeded_corpus_answers_the_enumeration_network_after_network() -> None:
    for graph in synthetic(25, seed=7):
        source, sink = min(graph.nodes()), max(graph.nodes())
        shipped = flow_map(graph, source, sink)
        assert max_flow(graph, source, sink) == min_cut(graph, source, sink)
        assert audit(graph, source, sink, shipped) == []
        for (start, end), amount in shipped.items():
            room = dict(graph.out_arcs(start))[end]
            assert 0 <= amount <= room

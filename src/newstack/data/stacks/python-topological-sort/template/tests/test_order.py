"""The order: predecessors-first, deterministic, honest about tangles."""

from __future__ import annotations

import pytest

from {{ package_name }}.corpus import synthetic
from {{ package_name }}.graph import Graph
from {{ package_name }}.order import (
    OrderError,
    block,
    order,
    validate,
)


def _lattice() -> Graph:
    graph = Graph()
    for source, target in ((1, 2), (1, 4), (2, 3), (4, 3), (3, 5), (4, 5)):
        graph.add_edge(source, target)
    graph.add_node(6)
    return graph


def test_a_ladder_lists_least_ready_first():
    assert order(_lattice()) == (1, 2, 4, 3, 5, 6)


def test_a_ladder_lists_every_node_once():
    graph = _lattice()
    listed = order(graph)
    assert sorted(listed) == sorted(graph.nodes())
    assert len(listed) == len(set(listed))


def test_the_order_is_a_fixed_point():
    graph = _lattice()
    assert order(graph) == order(graph)


def test_the_listing_validates_silent():
    graph = _lattice()
    assert validate(graph, order(graph)) == []


def test_a_broken_listing_is_named_broken():
    graph = Graph().add_edge(1, 2).add_edge(2, 3)
    assert validate(graph, (2, 1, 3))
    assert validate(graph, (1, 2))
    assert validate(graph, (1, 2, 3)) == []


def test_a_tangle_refuses_the_listing():
    ring = Graph().add_edge(4, 5).add_edge(5, 6).add_edge(6, 4)
    with pytest.raises(OrderError):
        order(ring)


def test_the_block_names_the_tangle():
    ring = Graph().add_edge(4, 5).add_edge(5, 6).add_edge(6, 4)
    assert block(ring) == (4, 5, 6)
    assert block(_lattice()) == ()


@pytest.mark.parametrize("seed", (3, 17, 99))
def test_a_seeded_corpus_orders_silent(seed):
    for graph in synthetic(10, seed=seed):
        listed = order(graph)
        assert validate(graph, listed) == []
        assert order(graph) == listed

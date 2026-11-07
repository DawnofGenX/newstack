"""The picker: the dumb fixed point the order must answer."""

from __future__ import annotations

import pytest

from {{ package_name }}.corpus import synthetic, tangles
from {{ package_name }}.graph import Graph
from {{ package_name }}.oracle import naive_order
from {{ package_name }}.order import order


def test_the_picker_answers_the_ladder():
    graph = Graph()
    for source, target in ((1, 2), (1, 4), (2, 3), (4, 3), (3, 5)):
        graph.add_edge(source, target)
    assert naive_order(graph) == (1, 2, 4, 3, 5)


def test_the_order_answers_the_picker():
    for graph in synthetic(25, seed=7):
        assert order(graph) == naive_order(graph)


def test_the_picker_stalls_on_a_tangle():
    for graph in tangles():
        with pytest.raises(ValueError):
            naive_order(graph)


def test_a_lone_node_picks_itself():
    lone = Graph()
    lone.add_node(4)
    assert naive_order(lone) == (4,)

"""The door: labels, pairs, the token face."""

from __future__ import annotations

import pytest

from {{ package_name }}.graph import (
    MAX_LABEL,
    MAX_NODES,
    Graph,
    GraphError,
    parse_graph,
)


def test_a_node_is_admitted_once():
    graph = Graph()
    graph.add_node(7).add_node(7)
    assert graph.nodes() == (7,)


def test_a_pair_admits_both_ends():
    graph = Graph().add_edge(2, 3)
    assert graph.nodes() == (2, 3)
    assert graph.edges() == ((2, 3),)
    assert graph.successors(2) == (3,)
    assert graph.predecessors(3) == (2,)


def test_labels_come_back_sorted():
    graph = Graph().add_edge(9, 1).add_edge(1, 5)
    assert graph.nodes() == (1, 5, 9)
    assert graph.successors(1) == (5,)


def test_a_float_label_is_refused():
    with pytest.raises(GraphError):
        Graph().add_node(1.5)


def test_a_past_ceiling_label_is_refused():
    with pytest.raises(GraphError):
        Graph().add_node(MAX_LABEL + 1)


def test_a_past_ceiling_count_is_refused():
    crowded = Graph()
    for node in range(MAX_NODES):
        crowded.add_node(node)
    with pytest.raises(GraphError):
        crowded.add_node(MAX_NODES)


def test_a_graph_survives_its_text_face():
    graph = Graph().add_edge(1, 2).add_edge(2, 3).add_node(8)
    assert parse_graph(graph.to_text()).edges() == graph.edges()


def test_a_half_pair_is_refused():
    with pytest.raises(GraphError):
        parse_graph("1>2>3")


def test_noise_is_no_graph():
    with pytest.raises(GraphError):
        parse_graph("a > b")
    with pytest.raises(GraphError):
        parse_graph("   ")

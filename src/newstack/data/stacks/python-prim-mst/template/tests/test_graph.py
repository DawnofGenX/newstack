from __future__ import annotations

from {{ package_name }}.graph import (
    MAX_LABEL,
    MAX_NODES,
    Graph,
    GraphError,
    ensure_label,
    ensure_weight,
    pair,
    parse_graph,
)


def build() -> Graph:
    graph = Graph()
    for low, high, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(low, high, weight)
    return graph


def test_a_node_is_admitted_once() -> None:
    graph = Graph().add_node(7).add_node(7)
    assert graph.nodes() == (7,)
    assert graph.has_node(7)
    assert not graph.has_node(8)


def test_an_edge_admits_both_ends_and_carries_its_weight() -> None:
    graph = Graph().add_edge(2, 3, 7)
    assert graph.nodes() == (2, 3)
    assert graph.edges() == (((2, 3), 7),)
    assert graph.neighbours(3) == ((2, 7),)


def test_an_edge_is_held_in_both_directions() -> None:
    graph = Graph().add_edge(2, 3, 7)
    assert graph.neighbours(2) == ((3, 7),)
    assert graph.neighbours(3) == ((2, 7),)


def test_edges_answer_each_edge_once_sorted() -> None:
    graph = Graph().add_edge(5, 1, 2).add_edge(1, 4, 1)
    assert graph.edges() == (((1, 4), 1), ((1, 5), 2))


def test_a_pair_is_directionless() -> None:
    assert pair(9, 2) == (2, 9)
    assert pair(2, 9) == (2, 9)


def test_a_loop_is_refused() -> None:
    try:
        Graph().add_edge(3, 3, 1)
    except GraphError:
        return
    raise AssertionError("a loop slipped in")


def test_a_re_weighted_edge_answers_the_last_word() -> None:
    graph = Graph().add_edge(2, 3, 7).add_edge(2, 3, 2)
    assert graph.edges() == (((2, 3), 2),)


def test_labels_and_weights_are_small_integers_only() -> None:
    assert ensure_label(7) == 7
    assert ensure_weight(0) == 0
    for noise in (1.5, "3", True, None):
        try:
            ensure_label(noise)
        except GraphError:
            pass
        else:
            raise AssertionError(f"{noise!r} slipped through the label door")


def test_weights_are_nonneg_and_bounded() -> None:
    assert ensure_weight(MAX_LABEL) == MAX_LABEL
    for noise in (-1, MAX_LABEL + 1, 1.5):
        try:
            ensure_weight(noise)
        except GraphError:
            pass
        else:
            raise AssertionError(f"{noise!r} slipped through the weight door")


def test_the_ceiling_holds_nodes_and_labels() -> None:
    crowded = Graph()
    for node in range(MAX_NODES):
        crowded.add_node(node)
    try:
        crowded.add_node(MAX_NODES)
    except GraphError:
        pass
    else:
        raise AssertionError("one node past the ceiling slipped in")
    try:
        ensure_label(MAX_LABEL + 1)
    except GraphError:
        pass
    else:
        raise AssertionError("a past-ceiling label slipped in")


def test_the_text_face_round_trips() -> None:
    lattice = build()
    assert parse_graph(lattice.to_text()).edges() == lattice.edges()


def test_the_parser_refuses_noise() -> None:
    for noise in ("1>2", "a > b", "  ", "1>2=x", "1.5>2=1"):
        try:
            parse_graph(noise)
        except GraphError:
            pass
        else:
            raise AssertionError(f"{noise!r} parsed as a graph")

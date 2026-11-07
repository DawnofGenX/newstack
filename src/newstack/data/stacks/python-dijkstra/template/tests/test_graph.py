from __future__ import annotations

from {{ package_name }}.graph import (
    MAX_LABEL,
    MAX_NODES,
    Graph,
    GraphError,
    ensure_label,
    ensure_weight,
    parse_graph,
)


def build() -> Graph:
    graph = Graph()
    for source, target, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(source, target, weight)
    graph.add_node(6)
    return graph


def test_a_node_is_admitted_once() -> None:
    graph = Graph().add_node(7).add_node(7)
    assert graph.nodes() == (7,)
    assert graph.has_node(7)
    assert not graph.has_node(8)


def test_an_edge_admits_both_ends_and_carries_its_weight() -> None:
    graph = Graph().add_edge(2, 3, 7)
    assert graph.nodes() == (2, 3)
    assert graph.edges() == ((2, 3, 7),)
    assert graph.successors(2) == ((3, 7),)


def test_a_re_weighted_edge_answers_the_last_word() -> None:
    graph = Graph().add_edge(2, 3, 7).add_edge(2, 3, 2)
    assert graph.edges() == ((2, 3, 2),)


def test_answers_come_back_sorted() -> None:
    graph = build()
    assert graph.nodes() == (1, 2, 3, 4, 5, 6)
    assert graph.successors(3) == ((5, 3),)
    assert graph.edges() == tuple(sorted(graph.edges()))


def test_successors_of_a_stranger_are_refused() -> None:
    try:
        Graph().successors(1)
    except GraphError:
        return
    raise AssertionError("a stranger walked in")


def test_floats_and_words_are_no_labels() -> None:
    for noise in (1.5, "a", None, True):
        try:
            Graph().add_node(noise)
        except GraphError:
            continue
        raise AssertionError(f"{noise!r} passed the door")


def test_negatives_and_floats_are_no_weights() -> None:
    for noise in (-1, 1.5, "a", None, True):
        try:
            Graph().add_edge(1, 2, noise)
        except GraphError:
            continue
        raise AssertionError(f"{noise!r} passed as a weight")


def test_a_past_ceiling_label_is_refused() -> None:
    try:
        ensure_label(MAX_LABEL + 1)
    except GraphError:
        return
    raise AssertionError("a giant label slipped in")


def test_a_past_ceiling_weight_is_refused() -> None:
    try:
        ensure_weight(MAX_LABEL + 1)
    except GraphError:
        return
    raise AssertionError("a giant weight slipped in")


def test_zero_is_a_honest_weight() -> None:
    assert ensure_weight(0) == 0
    assert Graph().add_edge(1, 2, 0).edges() == ((1, 2, 0),)


def test_the_node_ceiling_holds() -> None:
    crowded = Graph()
    for node in range(MAX_NODES):
        crowded.add_node(node)
    try:
        crowded.add_node(MAX_NODES)
    except GraphError:
        return
    raise AssertionError("the ceiling opened")


def test_a_graph_survives_its_text_face() -> None:
    graph = build()
    assert parse_graph(graph.to_text()).edges() == graph.edges()
    assert parse_graph(graph.to_text()).nodes() == graph.nodes()


def test_parse_accepts_nodes_and_edges_apart() -> None:
    graph = parse_graph("5 6 5>6=4")
    assert graph.edges() == ((5, 6, 4),)
    assert graph.nodes() == (5, 6)


def test_parse_refuses_a_mute_edge() -> None:
    try:
        parse_graph("1>2")
    except GraphError:
        return
    raise AssertionError("a weightless edge parsed")


def test_parse_refuses_noise() -> None:
    for noise in ("a", "1.5", "a>b=1", "1>2=-1", "", "1>2="):
        try:
            parse_graph(noise)
        except GraphError:
            continue
        raise AssertionError(f"{noise!r} parsed as a graph")

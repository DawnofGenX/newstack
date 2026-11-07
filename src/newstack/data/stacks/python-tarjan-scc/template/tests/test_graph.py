from __future__ import annotations

from {{ package_name }}.graph import (
    MAX_LABEL,
    MAX_NODES,
    Graph,
    GraphError,
    ensure_label,
    parse_graph,
)


def build() -> Graph:
    graph = Graph()
    for source, target in ((1, 2), (2, 3), (3, 1), (3, 4), (4, 5), (5, 4), (4, 6)):
        graph.add_edge(source, target)
    return graph


def test_a_node_is_admitted_once() -> None:
    graph = Graph().add_node(7).add_node(7)
    assert graph.nodes() == (7,)
    assert graph.has_node(7)
    assert not graph.has_node(8)


def test_an_edge_admits_both_ends() -> None:
    graph = Graph().add_edge(2, 3)
    assert graph.nodes() == (2, 3)
    assert graph.edges() == ((2, 3),)


def test_answers_come_back_sorted() -> None:
    graph = build()
    assert graph.nodes() == (1, 2, 3, 4, 5, 6)
    assert graph.successors(3) == (1, 4)
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


def test_a_past_ceiling_label_is_refused() -> None:
    try:
        ensure_label(MAX_LABEL + 1)
    except GraphError:
        return
    raise AssertionError("a giant label slipped in")


def test_the_node_ceiling_holds() -> None:
    crowded = Graph()
    for node in range(MAX_NODES):
        crowded.add_node(node)
    try:
        crowded.add_node(MAX_NODES)
    except GraphError:
        return
    raise AssertionError("the ceiling opened")


def test_repeated_adds_stay_quiet() -> None:
    first = build()
    again = build()
    assert first.edges() == again.edges()
    assert len(first) == 6


def test_a_graph_survives_its_text_face() -> None:
    graph = build()
    assert parse_graph(graph.to_text()).edges() == graph.edges()


def test_parse_accepts_nodes_and_edges_apart() -> None:
    graph = parse_graph("5 6 5>6")
    assert graph.edges() == ((5, 6),)
    assert graph.nodes() == (5, 6)


def test_parse_refuses_noise() -> None:
    for noise in ("a", "1.5", "a>b", ""):
        try:
            parse_graph(noise)
        except GraphError:
            continue
        raise AssertionError(f"{noise!r} parsed as a graph")

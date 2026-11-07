from __future__ import annotations

from {{ package_name }}.graph import (
    MAX_LABEL,
    MAX_NODES,
    MAX_WEIGHT,
    Graph,
    GraphError,
    ensure_label,
    ensure_weight,
    parse_graph,
)


def build() -> Graph:
    graph = Graph()
    for source, target, weight in (
        (1, 2, 4),
        (2, 3, -2),
        (3, 4, 3),
        (1, 3, 5),
        (2, 4, 1),
    ):
        graph.add_edge(source, target, weight)
    return graph


def test_a_node_is_admitted_once() -> None:
    graph = Graph().add_node(7).add_node(7)
    assert graph.nodes() == (7,)
    assert graph.has_node(7)
    assert not graph.has_node(8)


def test_an_edge_admits_both_ends_and_its_weight() -> None:
    graph = Graph().add_edge(2, 3, -7)
    assert graph.nodes() == (2, 3)
    assert graph.edges() == ((2, 3, -7),)
    assert graph.weight(2, 3) == -7


def test_answers_come_back_sorted() -> None:
    graph = build()
    assert graph.nodes() == (1, 2, 3, 4)
    assert graph.successors(2) == (3, 4)
    assert graph.edges() == tuple(sorted(graph.edges()))


def test_successors_of_a_stranger_are_refused() -> None:
    try:
        Graph().successors(1)
    except GraphError:
        return
    raise AssertionError("a stranger walked in")


def test_a_missing_edge_is_named() -> None:
    try:
        build().weight(4, 1)
    except GraphError:
        return
    raise AssertionError("an absent edge answered")


def test_floats_and_words_are_no_labels_or_weights() -> None:
    for noise in (1.5, "a", None, True):
        try:
            Graph().add_node(noise)
        except GraphError:
            continue
        raise AssertionError(f"{noise!r} passed the door")
    try:
        Graph().add_edge(1, 2, 0.5)
    except GraphError:
        return
    raise AssertionError("a float weight passed the door")


def test_a_past_ceiling_label_is_refused() -> None:
    try:
        ensure_label(MAX_LABEL + 1)
    except GraphError:
        return
    raise AssertionError("a giant label slipped in")


def test_a_past_ceiling_weight_is_refused() -> None:
    for ceiling in (-MAX_WEIGHT - 1, MAX_WEIGHT + 1):
        try:
            ensure_weight(ceiling)
        except GraphError:
            continue
        raise AssertionError(f"{ceiling} slipped in")


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


def test_parse_accepts_nodes_and_weighted_edges_apart() -> None:
    graph = parse_graph("5 6 5>6=-4")
    assert graph.edges() == ((5, 6, -4),)
    assert graph.nodes() == (5, 6)


def test_parse_refuses_noise() -> None:
    for noise in ("a", "1.5", "a>b", "", "1>2", "1>2=x"):
        try:
            parse_graph(noise)
        except GraphError:
            continue
        raise AssertionError(f"{noise!r} parsed as a graph")

from __future__ import annotations

from {{ package_name }}.graph import (
    MAX_LABEL,
    MAX_NODES,
    Graph,
    GraphError,
    hop,
    parse_graph,
)


def lattice() -> Graph:
    graph = Graph()
    for source, target, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(source, target, weight)
    return graph


def test_the_arrow_is_held_one_way() -> None:
    graph = Graph().add_edge(2, 3, 7)
    assert graph.neighbours(2) == ((3, 7),)
    assert graph.neighbours(3) == ()


def test_an_arrow_is_answered_once() -> None:
    assert Graph().add_edge(2, 3, 7).edges() == (((2, 3), 7),)


def test_two_arrows_between_a_pair_are_two_edges() -> None:
    graph = Graph().add_edge(2, 3, 7).add_edge(3, 2, 1)
    assert graph.edges() == (((2, 3), 7), ((3, 2), 1))


def test_labels_come_back_sorted() -> None:
    assert Graph().add_edge(9, 1, 2).nodes() == (1, 9)


def test_hop_keeps_the_direction() -> None:
    assert hop(9, 1) == (9, 1)


def test_a_loop_is_refused() -> None:
    try:
        Graph().add_edge(3, 3, 1)
    except GraphError:
        pass
    else:
        raise AssertionError("a loop was held")


def test_a_graph_survives_its_text_face() -> None:
    assert parse_graph(lattice().to_text()).edges() == lattice().edges()


def test_a_weightless_arrow_is_refused() -> None:
    try:
        parse_graph("1>2")
    except GraphError:
        pass
    else:
        raise AssertionError("a mute arrow was parsed")


def test_a_negative_weight_is_refused() -> None:
    try:
        Graph().add_edge(1, 2, -1)
    except GraphError:
        pass
    else:
        raise AssertionError("a negative weight was held")


def test_the_door_keeps_its_ceilings() -> None:
    assert MAX_LABEL == 999
    assert MAX_NODES == 32

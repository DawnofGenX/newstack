from __future__ import annotations

from {{ package_name }}.graph import (
    MAX_LABEL,
    MAX_NODES,
    Graph,
    GraphError,
    parse_graph,
)


def diamond() -> Graph:
    graph = Graph()
    for start, end, room in (
        (0, 1, 3), (1, 3, 2), (0, 2, 2), (2, 3, 3), (0, 3, 1), (1, 2, 1),
    ):
        graph.add_edge(start, end, room)
    return graph


def test_a_node_is_admitted_once() -> None:
    assert Graph().add_node(7).add_node(7).nodes() == (7,)


def test_an_arc_admits_both_ends() -> None:
    assert Graph().add_edge(2, 3, 1).nodes() == (2, 3)


def test_an_arc_is_held_one_way_only() -> None:
    graph = Graph().add_edge(2, 3, 7)
    assert graph.out_arcs(2) == ((3, 7),)
    assert graph.out_arcs(3) == ()


def test_a_repeated_arc_merges_its_capacity() -> None:
    assert Graph().add_edge(2, 3, 4).add_edge(2, 3, 5).out_arcs(2) == ((3, 9),)


def test_the_opposite_arc_of_a_channel_is_refused() -> None:
    try:
        Graph().add_edge(2, 3, 1).add_edge(3, 2, 1)
    except GraphError:
        pass
    else:
        raise AssertionError("a two-way channel stood")


def test_a_loop_is_refused() -> None:
    try:
        Graph().add_edge(3, 3, 1)
    except GraphError:
        pass
    else:
        raise AssertionError("a loop stood")


def test_labels_and_capacities_stay_small_integers() -> None:
    for bad_call in (lambda: Graph().add_node(1.5), lambda: Graph().add_edge(1, 2, 1.5),
                     lambda: Graph().add_edge(1, 2, -1),
                     lambda: Graph().add_node(MAX_LABEL + 1)):
        try:
            bad_call()
        except GraphError:
            continue
        raise AssertionError("noise stood at the door")


def test_the_ceiling_holds_past_the_last_node() -> None:
    crowded = Graph()
    for node in range(MAX_NODES):
        crowded.add_node(node)
    try:
        crowded.add_node(MAX_NODES)
    except GraphError:
        pass
    else:
        raise AssertionError("a thirty-third node stood")


def test_a_network_survives_its_text_face() -> None:
    assert parse_graph(diamond().to_text()).edges() == diamond().edges()


def test_a_capacityless_arc_speaks_no_network() -> None:
    try:
        parse_graph("1>2")
    except GraphError:
        pass
    else:
        raise AssertionError("a mute arc parsed")


def test_noise_and_nothing_parse_to_nothing() -> None:
    for text in ("a > b", "  ", "1.5"):
        try:
            parse_graph(text)
        except GraphError:
            continue
        raise AssertionError(f"{text!r} parsed to a network")

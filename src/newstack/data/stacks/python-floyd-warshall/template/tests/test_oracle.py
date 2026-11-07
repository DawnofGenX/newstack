from __future__ import annotations

from {{ package_name }}.graph import (
    Graph,
)
from {{ package_name }}.oracle import (
    MAX_SWEEPS,
    distance_table,
    oracle_table,
    walk_from,
)


def lattice() -> Graph:
    graph = Graph()
    for source, target, weight in (
        (1, 2, 4), (2, 3, 1), (1, 4, 2), (4, 3, 1), (3, 5, 3), (4, 5, 8),
    ):
        graph.add_edge(source, target, weight)
    return graph


def test_the_walk_answers_the_roads_it_walks() -> None:
    walked = walk_from(lattice(), 1)
    assert walked == {1: 0, 2: 4, 3: 3, 4: 2, 5: 6}


def test_the_source_stands_at_zero() -> None:
    assert walk_from(lattice(), 3)[3] == 0


def test_the_table_keeps_its_pairs_ordered() -> None:
    table = distance_table(lattice())
    assert (1, 5) in table and (5, 1) not in table


def test_the_walkers_table_is_its_own_answer() -> None:
    assert oracle_table(lattice()) == distance_table(lattice())


def test_a_one_way_arrow_walks_forward_only() -> None:
    assert distance_table(Graph().add_edge(1, 2, 3)) == {
        (1, 1): 0, (1, 2): 3, (2, 2): 0,
    }


def test_a_lone_node_walks_itself() -> None:
    lone = Graph()
    lone.add_node(4)
    assert distance_table(lone) == {(4, 4): 0}


def test_a_stranger_walks_nothing() -> None:
    try:
        walk_from(lattice(), 99)
    except KeyError:
        pass
    else:
        raise AssertionError("a stranger walked a road")


def test_the_walk_rests_inside_its_ceiling() -> None:
    assert MAX_SWEEPS >= 4 * MAX_SWEEPS // 4
    assert len(lattice()) < MAX_SWEEPS

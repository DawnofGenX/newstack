from __future__ import annotations

import pytest

from {{ package_name }}.graph import (
    Graph,
)
from {{ package_name }}.oracle import (
    OracleError,
    cut_capacity,
    cuts,
    least_cut,
    min_cut,
    oracle_value,
)


def diamond() -> Graph:
    graph = Graph()
    for start, end, room in (
        (0, 1, 3), (1, 3, 2), (0, 2, 2), (2, 3, 3), (0, 3, 1), (1, 2, 1),
    ):
        graph.add_edge(start, end, room)
    return graph


def test_the_enumeration_draws_a_cut_per_shore() -> None:
    assert len(cuts(diamond(), 0, 3)) == 4


def test_the_enumerations_least_is_the_walkers_value() -> None:
    from {{ package_name }}.solve import max_flow

    assert min_cut(diamond(), 0, 3) == max_flow(diamond(), 0, 3) == 6


def test_the_oracle_answers_the_same_least() -> None:
    assert oracle_value(diamond(), 0, 3) == min_cut(diamond(), 0, 3)


def test_the_least_cut_names_its_shore() -> None:
    assert least_cut(diamond(), 0, 3) == (6, (0,))


def test_a_named_shore_pays_its_crossing() -> None:
    assert cut_capacity(diamond(), {0, 1}) == 6


def test_a_pair_cuts_at_its_arc() -> None:
    assert min_cut(Graph().add_edge(1, 2, 5), 1, 2) == 5


def test_a_network_with_no_route_cuts_to_zero() -> None:
    apart = Graph().add_edge(1, 2, 4).add_node(8)
    assert min_cut(apart, 1, 8) == 0


def test_ends_that_match_cut_nothing() -> None:
    with pytest.raises(OracleError):
        min_cut(diamond(), 0, 0)


def test_a_stranger_is_no_end() -> None:
    with pytest.raises(KeyError):
        min_cut(diamond(), 99, 3)

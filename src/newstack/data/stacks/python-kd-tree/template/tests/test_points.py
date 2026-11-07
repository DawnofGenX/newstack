from __future__ import annotations

import pytest

from {{ package_name }}.points import (
    MAX_COORD,
    PointError,
    describe,
    ensure_point,
    ensure_rect,
)


def test_a_pair_comes_back_itself() -> None:
    assert ensure_point((3, -4)) == (3, -4)
    assert ensure_point((0, 0)) == (0, 0)


def test_the_plane_edge_is_the_last_valid_coordinate() -> None:
    assert ensure_point((MAX_COORD, -MAX_COORD)) == (MAX_COORD, -MAX_COORD)
    with pytest.raises(PointError):
        ensure_point((MAX_COORD + 1, 0))
    with pytest.raises(PointError):
        ensure_point((0, -MAX_COORD - 1))


@pytest.mark.parametrize(
    "bad",
    [
        (1.5, 2),
        (1, 2.0),
        (True, 1),
        (1, False),
        (1,),
        (1, 2, 3),
        "1,2",
        7,
        None,
        [1, 2],
    ],
)
def test_the_gate_refuses_every_impostor(bad: object) -> None:
    with pytest.raises(PointError):
        ensure_point(bad)


def test_a_rectangle_needs_four_integers_in_order() -> None:
    assert ensure_rect((-9, -9, 9, 9)) == (-9, -9, 9, 9)
    assert ensure_rect((5, 5, 5, 5)) == (5, 5, 5, 5)
    with pytest.raises(PointError):
        ensure_rect((5, 0, 0, 5))
    with pytest.raises(PointError):
        ensure_rect((0, 5, 5, 0))
    with pytest.raises(PointError):
        ensure_rect((0, 0, 0))
    with pytest.raises(PointError):
        ensure_rect((0.0, 0, 1, 1))


def test_describe_prints_the_pair_the_cli_prints() -> None:
    assert describe((-4, 7)) == "(-4, 7)"
    assert describe((0, 0)) == "(0, 0)"

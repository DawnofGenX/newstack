from __future__ import annotations

import pytest

from {{ package_name }} import stamp as subject

Stamp = subject.Stamp


def test_the_order_is_physical_then_logical_then_node() -> None:
    assert Stamp(10, 1, "a") < Stamp(10, 2, "a")
    assert Stamp(10, 9, "a") < Stamp(11, 0, "a")
    assert Stamp(10, 1, "a") < Stamp(10, 1, "b")


def test_the_same_point_on_two_nodes_is_still_ordered() -> None:
    left, right = Stamp(10, 0, "alpha"), Stamp(10, 0, "beta")
    assert left != right
    assert sorted([right, left]) == [left, right]


def test_text_round_trips() -> None:
    stamp = Stamp(1_700_000_000_000, 3, "node-a")
    assert subject.parse_stamp(stamp.text()) == stamp


def test_text_sorts_like_the_stamp() -> None:
    stamps = [Stamp(10, 0, "b"), Stamp(9, 5, "a"), Stamp(10, 0, "a"), Stamp(10, 1, "a")]
    assert [stamp.text() for stamp in sorted(stamps)] == [
        stamp.text() for stamp in sorted(stamps, key=lambda item: item.text())
    ]


def test_the_key_is_the_order_you_would_write_down() -> None:
    assert Stamp(7, 2, "z").key() == (7, 2, "z")


def test_a_negative_physical_time_is_refused() -> None:
    with pytest.raises(subject.StampError, match="negative"):
        Stamp(-1)


def test_a_boolean_is_not_a_timestamp() -> None:
    with pytest.raises(subject.StampError, match="whole number"):
        Stamp(True)  # type: ignore[arg-type]


def test_a_node_name_cannot_break_the_text_form() -> None:
    with pytest.raises(subject.StampError, match="node name"):
        Stamp(1, 0, "a|b")


def test_parsing_refuses_text_that_is_not_a_stamp() -> None:
    with pytest.raises(subject.StampError, match="is not a stamp"):
        subject.parse_stamp("1700000000000@a")

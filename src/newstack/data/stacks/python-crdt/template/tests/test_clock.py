import pytest

from {{ package_name }} import clock as subject


def test_stamps_order_by_millisecond() -> None:
    assert subject.Stamp(1_000, "a") < subject.Stamp(1_001, "a")


def test_the_node_breaks_a_millisecond_tie() -> None:
    assert subject.Stamp(1_000, "a") < subject.Stamp(1_000, "b")


def test_a_stamp_round_trips() -> None:
    stamp = subject.Stamp(1_700_000_000_000, "node-1")
    assert subject.Stamp.parse(stamp.as_list()) == stamp


def test_a_negative_stamp_is_refused() -> None:
    with pytest.raises(subject.ClockError):
        subject.Stamp(-1, "a")


def test_a_nameless_stamp_is_refused() -> None:
    with pytest.raises(subject.ClockError):
        subject.Stamp(1, "")


def test_a_stamp_of_the_wrong_shape_is_refused() -> None:
    with pytest.raises(subject.ClockError):
        subject.Stamp.parse([1])

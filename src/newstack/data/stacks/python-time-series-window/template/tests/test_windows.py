import pytest

from {{ package_name }} import events as events_mod
from {{ package_name }} import windows as subject

SECOND = events_mod.US
BASE = 1_767_225_600 * SECOND


def test_alignment_belongs_to_the_epoch() -> None:
    assert subject.align(BASE + 7 * SECOND, 60 * SECOND) == BASE


def test_a_window_is_half_open() -> None:
    window = subject.Window(BASE, BASE + 60 * SECOND)
    assert BASE in window
    assert BASE + 59 * SECOND in window
    assert BASE + 60 * SECOND not in window


def test_a_tiling_instant_lands_in_one_window() -> None:
    assert len(subject.containing(BASE + 5 * SECOND, 60 * SECOND)) == 1


def test_a_hop_boundary_lands_in_two() -> None:
    windows = subject.containing(BASE + 60 * SECOND, 60 * SECOND, 30 * SECOND)
    assert len(windows) == 2


def test_a_hop_wider_than_the_window_is_refused() -> None:
    with pytest.raises(subject.WindowError):
        subject.containing(BASE, 60 * SECOND, 120 * SECOND)


def test_an_empty_window_is_refused() -> None:
    with pytest.raises(subject.WindowError):
        subject.Window(BASE, BASE)


def test_covering_counts_the_windows() -> None:
    assert len(subject.covering(BASE, BASE + 120 * SECOND, 60 * SECOND)) == 3


def test_an_inverted_covering_range_is_refused() -> None:
    with pytest.raises(subject.WindowError):
        subject.covering(BASE, BASE - 1, 60 * SECOND)

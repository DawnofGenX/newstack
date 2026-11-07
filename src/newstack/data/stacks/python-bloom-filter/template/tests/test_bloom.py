"""The array's promise: added keys answer present, always, one way only."""

from __future__ import annotations

import pytest

from {{ package_name }}.bloom import (
    MAX_ROWS,
    MAX_WIDTH,
    ROWS,
    SEED,
    WIDTH,
    Bloom,
    BloomError,
)
from {{ package_name }}.universe import UNIVERSE

KEYS = (0, 1, 7, 64, 127, 128, 200, 255)


def test_an_added_key_is_never_answered_absent() -> None:
    bloom = Bloom()
    for key in KEYS:
        bloom.add(key)
        assert bloom.might_contain(key)
    assert bloom.audit() == []


def test_add_reports_its_fresh_bits_within_the_rows() -> None:
    bloom = Bloom()
    for key in KEYS:
        assert 0 <= bloom.add(key) <= ROWS


def test_re_adding_changes_nothing_but_stores_no_twin() -> None:
    bloom = Bloom()
    for key in KEYS:
        bloom.add(key)
    bits = bloom.bits
    for key in KEYS:
        bloom.add(key)
    assert bloom.bits == bits
    assert len(bloom.added) == len(set(bloom.added)) == len(KEYS)


def test_absence_points_at_a_row_never_raised() -> None:
    bloom = Bloom(64, 4, 7)
    for key in range(256):
        if not bloom.might_contain(key):
            row = bloom.first_clear_row(key)
            assert row is not None


def test_the_lie_runs_one_way_only() -> None:
    bloom = Bloom(64, 4, 7)
    for key in (165, 242, 38, 101):
        bloom.add(key)
    for key in bloom.survey():
        assert key not in bloom.added
        assert bloom.might_contain(key)
        assert bloom.first_clear_row(key) is None


def test_the_pattern_round_trips_through_a_file() -> None:
    bloom = Bloom()
    for key in KEYS:
        bloom.add(key)
    twin = Bloom.from_dict(bloom.as_dict())
    assert twin.bits == bloom.bits
    assert twin.added == bloom.added
    assert twin.audit() == []


def test_a_broken_file_is_named_not_guessed() -> None:
    with pytest.raises(BloomError):
        Bloom.from_dict({})
    with pytest.raises(BloomError):
        Bloom.from_dict("nope")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"width": 7},
        {"width": MAX_WIDTH + 1},
        {"rows": 0},
        {"rows": MAX_ROWS + 1},
        {"width": 8, "bits": 256},
        {"width": 8, "bits": -1},
    ],
)
def test_the_shape_is_documented_and_policed(kwargs: dict[str, int]) -> None:
    with pytest.raises(BloomError):
        Bloom(**kwargs)


def test_a_negative_seat_seed_leaves_before_the_shape() -> None:
    from {{ package_name }}.universe import UniverseError

    with pytest.raises(UniverseError):
        Bloom(seed=-1)


def test_the_shipped_shape_is_the_documented_one() -> None:
    bloom = Bloom()
    assert (bloom.width, bloom.rows, bloom.seed) == (WIDTH, ROWS, SEED) == (1024, 4, 11)


def test_the_empty_array_asks_nothing_and_hides_nothing() -> None:
    bloom = Bloom()
    assert bloom.survey() == []
    assert bloom.bits_set == 0
    assert not bloom.might_contain(0)


def test_the_whole_universe_seats_inside_the_documented_width() -> None:
    bloom = Bloom()
    for key in range(UNIVERSE):
        assert all(0 <= seat < bloom.width for seat in bloom.seats_of(key))

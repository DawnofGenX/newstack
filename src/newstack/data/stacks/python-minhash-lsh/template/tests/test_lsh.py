import itertools

import pytest

from {{ package_name }} import lsh as subject


def test_the_width_is_bands_times_rows() -> None:
    assert subject.Bands(8, 16).width == 128


def test_zero_bands_is_refused() -> None:
    with pytest.raises(subject.LshError, match="at least one band"):
        subject.Bands(0, 16)


def test_zero_rows_is_refused() -> None:
    with pytest.raises(subject.LshError, match="at least one row"):
        subject.Bands(8, 0)


def test_the_probability_at_zero_is_zero() -> None:
    assert subject.Bands(8, 16).probability(0.0) == 0.0


def test_the_probability_at_one_is_one() -> None:
    assert subject.Bands(8, 16).probability(1.0) == pytest.approx(1.0)


def test_the_threshold_is_where_half_the_pairs_become_candidates() -> None:
    bands = subject.Bands(8, 16)
    assert bands.probability(bands.threshold()) == pytest.approx(0.5)


def test_the_curve_rises() -> None:
    curve = subject.Bands(8, 16).curve(7)
    rises = [low[1] <= high[1] + 1e-12 for low, high in itertools.pairwise(curve)]
    assert all(rises)


def test_more_bands_lower_the_threshold() -> None:
    assert subject.Bands(32, 4).threshold() < subject.Bands(4, 32).threshold()


def test_a_short_signature_is_refused() -> None:
    with pytest.raises(subject.LshError, match=r"needs 128 positions"):
        subject.Bands(8, 16).buckets(tuple(range(16)))


def test_identical_signatures_are_candidates() -> None:
    signature = tuple(range(32))
    pairs = subject.Bands(4, 8).candidates({"a": signature, "b": signature})
    assert pairs == [("a", "b")]


def test_pick_uses_the_whole_width() -> None:
    bands = subject.pick(128, 0.8)
    assert bands.width == 128
    assert bands.bands * bands.rows == 128


def test_pick_lands_near_the_requested_threshold() -> None:
    assert subject.pick(128, 0.5).threshold() < subject.pick(128, 0.9).threshold()


def test_a_threshold_outside_zero_to_one_is_refused() -> None:
    with pytest.raises(subject.LshError, match=r"0\.\.1"):
        subject.Bands(8, 16).probability(1.5)

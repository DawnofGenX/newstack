"""The generator has to be the same on every interpreter, or published numbers drift."""

import pytest

from {{ package_name }} import rng as subject


def test_the_same_seed_gives_the_same_stream():
    left, right = subject.Rng(7), subject.Rng(7)
    assert [left.next_u64() for _ in range(5)] == [right.next_u64() for _ in range(5)]


def test_different_seeds_diverge():
    assert subject.Rng(7).next_u64() != subject.Rng(8).next_u64()


def test_the_stream_advances():
    stream = subject.Rng(1)
    values = [stream.next_u64() for _ in range(4)]
    assert len(set(values)) == 4
    assert all(value == value & subject.MASK for value in values)


def test_random_stays_inside_the_unit_interval():
    stream = subject.Rng(3)
    draws = [stream.random() for _ in range(200)]
    assert all(0.0 <= value < 1.0 for value in draws)
    assert 0.4 < sum(draws) / len(draws) < 0.6


def test_below_covers_its_whole_range_and_nothing_else():
    stream = subject.Rng(11)
    seen = {stream.below(6) for _ in range(500)}
    assert seen == set(range(6))


def test_a_zero_bound_is_refused():
    with pytest.raises(subject.RngError, match="at least 1"):
        subject.Rng(1).below(0)


def test_a_negative_bound_is_refused():
    with pytest.raises(subject.RngError):
        subject.Rng(1).below(-3)

from __future__ import annotations

import pytest

from {{ package_name }} import rng as subject

MASK = subject.MASK
Rng = subject.Rng


def test_the_stream_repeats_for_one_seed() -> None:
    first, second = Rng(11), Rng(11)
    assert [first.next_u64() for _ in range(5)] == [second.next_u64() for _ in range(5)]


def test_different_seeds_diverge() -> None:
    left, right = Rng(1), Rng(2)
    assert left.next_u64() != right.next_u64()


def test_values_stay_inside_the_word() -> None:
    stream = Rng(3)
    values = [stream.next_u64() for _ in range(200)]
    assert all(0 <= value <= MASK for value in values)
    assert len(set(values)) == len(values)


def test_random_is_half_open() -> None:
    stream = Rng(5)
    draws = [stream.random() for _ in range(500)]
    assert all(0.0 <= draw < 1.0 for draw in draws)
    assert min(draws) < 0.1 and max(draws) > 0.9


def test_uniform_stays_inside_its_bounds() -> None:
    stream = Rng(7)
    draws = [stream.uniform(2.0, 5.0) for _ in range(200)]
    assert all(2.0 <= draw <= 5.0 for draw in draws)
    assert min(draws) < 3.0 and max(draws) > 4.0


def test_a_reversed_range_is_refused() -> None:
    with pytest.raises(ValueError, match="reversed"):
        Rng(1).uniform(5.0, 2.0)


def test_a_non_integer_seed_is_refused() -> None:
    with pytest.raises(TypeError):
        Rng(1.5)  # type: ignore[arg-type]

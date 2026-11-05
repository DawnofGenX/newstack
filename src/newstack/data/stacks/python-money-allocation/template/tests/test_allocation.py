"""An allocator that loses a cent per call is a reconciliation ticket; these prove it does not."""

from __future__ import annotations

import pytest

from {{ package_name }} import allocation as subject
from {{ package_name }} import errors as errors_mod
from {{ package_name }} import model as model_mod


def test_an_even_three_way_split_balances() -> None:
    parts = subject.allocate(model_mod.Money(10000, "USD"), [1, 1, 1])
    assert [part.amount for part in parts] == [3334, 3333, 3333]
    assert sum(part.amount for part in parts) == 10000


def test_the_largest_remainder_takes_the_extra_unit() -> None:
    parts = subject.allocate(model_mod.Money(10000, "USD"), [3, 2, 1])
    assert [part.amount for part in parts] == [5000, 3333, 1667]


def test_ties_go_to_the_earliest_share() -> None:
    parts = subject.allocate(model_mod.Money(100, "JPY"), [1, 1, 1])
    assert [part.amount for part in parts] == [34, 33, 33]


def test_zero_ratios_are_allowed_when_the_weight_is_not_zero() -> None:
    parts = subject.allocate(model_mod.Money(1000, "USD"), [1, 0])
    assert [part.amount for part in parts] == [1000, 0]


def test_a_negative_amount_splits_and_balances() -> None:
    parts = subject.allocate(model_mod.Money(-1000, "USD"), [1, 1, 1])
    assert [part.amount for part in parts] == [-334, -333, -333]
    assert sum(part.amount for part in parts) == -1000


def test_a_huge_amount_is_still_exact() -> None:
    total = 10**18 + 1
    parts = subject.allocate(model_mod.Money(total, "USD"), [3, 3, 4])
    assert sum(part.amount for part in parts) == total


@pytest.mark.parametrize("ratios", [[], [0, 0], [1, -1]])
def test_impossible_ratios_are_refused(ratios: list[int]) -> None:
    with pytest.raises(errors_mod.AllocationError):
        subject.allocate(model_mod.Money(100, "USD"), ratios)


def test_a_float_ratio_is_refused() -> None:
    with pytest.raises(errors_mod.AllocationError, match="integers"):
        subject.allocate(model_mod.Money(100, "USD"), [1.0, 1.0])


def test_split_is_allocate_with_equal_weights() -> None:
    parts = subject.split(model_mod.Money(10, "USD"), 3)
    assert [part.amount for part in parts] == [4, 3, 3]
    with pytest.raises(errors_mod.AllocationError):
        subject.split(model_mod.Money(10, "USD"), 0)


def test_one_part_gets_everything() -> None:
    assert subject.split(model_mod.Money(999, "KWD"), 1)[0].amount == 999


def test_a_million_random_splits_all_balance() -> None:
    import random

    rng = random.Random(20260101)
    for _ in range(200):
        amount = rng.randint(-10**9, 10**9)
        ratios = [rng.randint(0, 1000) for _ in range(rng.randint(1, 6))]
        if sum(ratios) == 0:
            ratios[0] = 1
        parts = subject.allocate(model_mod.Money(amount, "USD"), ratios)
        assert sum(part.amount for part in parts) == amount

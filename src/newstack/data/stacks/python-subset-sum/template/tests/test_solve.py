from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    MAX_TARGET,
    MAX_VALUE,
    MAX_VALUES,
    SubsetSumError,
    audit,
    solve,
    witness,
)


def test_empty_zero() -> None:
    assert solve([], 0) is True


def test_single_match() -> None:
    assert solve([5], 5) is True


def test_single_no() -> None:
    assert solve([5], 3) is False


def test_no_match() -> None:
    assert solve([1, 2], 4) is False


def test_classic() -> None:
    assert solve([3, 34, 4, 12, 5, 2], 9) is True


def test_witness_sum() -> None:
    w = witness([3, 34, 4, 12, 5, 2], 9)
    assert sum(w) == 9


def test_audit_clean() -> None:
    assert audit([3, 34, 4, 12, 5, 2], 9) == []


def test_too_many() -> None:
    with pytest.raises(SubsetSumError):
        solve([0] * (MAX_VALUES + 1), 0)


def test_empty_target_bad() -> None:
    with pytest.raises(SubsetSumError):
        solve([1], -1)


def test_too_large_target() -> None:
    with pytest.raises(SubsetSumError):
        solve([1], MAX_TARGET + 1)


def test_too_large_value() -> None:
    with pytest.raises(SubsetSumError):
        solve([MAX_VALUE + 1], 1)


def test_negative_value() -> None:
    with pytest.raises(SubsetSumError):
        solve([-1], 0)


def test_zero_target() -> None:
    assert solve([1, 2], 0) is True


def test_witness_empty_on_false() -> None:
    assert witness([1, 2], 4) == []


def test_witness_subsequence() -> None:
    vs = [3, 34, 4, 12, 5, 2]
    w = witness(vs, 9)
    it = iter(vs)
    for x in w:
        while True:
            y = next(it)
            if y == x:
                break


def test_audit_false() -> None:
    assert audit([1, 2], 4) == []


def test_all_values() -> None:
    assert solve([1, 2, 3], 6) is True


def test_large_target_false() -> None:
    assert solve([1, 2], 10) is False


def test_duplicate_values() -> None:
    assert solve([2, 2], 4) is True

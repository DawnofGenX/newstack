from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    MAX_VALUE,
    MAX_VALUES,
    MaxSubarrayError,
    audit,
    solve,
    witness,
)


def test_single() -> None:
    assert solve([5]) == 5


def test_classic() -> None:
    assert solve([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6


def test_all_negative() -> None:
    assert solve([-3, -2, -5]) == -2


def test_witness_sum() -> None:
    w = witness([-2, 1, -3, 4, -1, 2, 1, -5, 4])
    assert sum(w) == 6


def test_audit_clean() -> None:
    assert audit([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == []


def test_empty() -> None:
    with pytest.raises(MaxSubarrayError):
        solve([])


def test_too_many() -> None:
    with pytest.raises(MaxSubarrayError):
        solve([0] * (MAX_VALUES + 1))


def test_too_large_value() -> None:
    with pytest.raises(MaxSubarrayError):
        solve([MAX_VALUE + 1])


def test_witness_contiguous() -> None:
    vs = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    w = witness(vs)
    assert w in [vs[i : i + len(w)] for i in range(len(vs) - len(w) + 1)]


def test_two_values() -> None:
    assert solve([1, 2]) == 3


def test_negative_then_positive() -> None:
    assert solve([-5, 10]) == 10


def test_audit_negative() -> None:
    assert audit([-3, -2, -5]) == []

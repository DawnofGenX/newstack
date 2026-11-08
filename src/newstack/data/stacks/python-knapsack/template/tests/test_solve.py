from __future__ import annotations

from {{ package_name }}.solve import (
    MAX_ITEMS,
    KnapsackError,
    audit,
    solve,
    witness,
)


def test_empty() -> None:
    assert solve([], [], 5) == 0


def test_single_fits() -> None:
    assert solve([2], [3], 5) == 3


def test_single_heavy() -> None:
    assert solve([6], [3], 5) == 0


def test_classic() -> None:
    assert solve([2, 3, 4], [3, 4, 5], 5) == 7


def test_witness() -> None:
    w = witness([2, 3, 4], [3, 4, 5], 5)
    assert sum([3, 4, 5][i] for i in w) == 7


def test_audit_clean() -> None:
    assert audit([2, 3, 4], [3, 4, 5], 5) == []


def test_too_many() -> None:
    import pytest

    with pytest.raises(KnapsackError):
        solve([1] * (MAX_ITEMS + 1), [1] * (MAX_ITEMS + 1), 5)


def test_bad_capacity() -> None:
    import pytest

    with pytest.raises(KnapsackError):
        solve([1], [1], -1)

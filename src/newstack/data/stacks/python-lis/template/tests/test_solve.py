from __future__ import annotations

from {{ package_name }}.solve import (
    MAX_VALUE,
    MAX_VALUES,
    LISError,
    audit,
    solve,
    witness,
)


def test_single() -> None:
    assert solve([5]) == 1


def test_increasing() -> None:
    assert solve([1, 2, 3]) == 3


def test_decreasing() -> None:
    assert solve([3, 2, 1]) == 1


def test_classic() -> None:
    assert solve([10, 9, 2, 5, 3, 7, 101, 18]) == 4


def test_duplicates_not_counted() -> None:
    assert solve([1, 1, 1]) == 1


def test_witness_increasing() -> None:
    w = witness([10, 9, 2, 5, 3, 7, 101, 18])
    assert all(w[k] < w[k + 1] for k in range(len(w) - 1))


def test_witness_length() -> None:
    w = witness([10, 9, 2, 5, 3, 7, 101, 18])
    assert len(w) == solve([10, 9, 2, 5, 3, 7, 101, 18])


def test_audit_clean() -> None:
    assert audit([1, 2, 3]) == []


def test_too_many() -> None:
    import pytest

    with pytest.raises(LISError):
        solve([0] * (MAX_VALUES + 1))


def test_empty() -> None:
    import pytest

    with pytest.raises(LISError):
        solve([])


def test_too_large() -> None:
    import pytest

    with pytest.raises(LISError):
        solve([MAX_VALUE + 1])


def test_negative() -> None:
    import pytest

    with pytest.raises(LISError):
        solve([-1])


def test_witness_empty_raises() -> None:
    import pytest

    with pytest.raises(LISError):
        witness([])


def test_single_witness() -> None:
    assert witness([7]) == [7]


def test_equal_values() -> None:
    assert solve([2, 2]) == 1


def test_audit_empty() -> None:
    assert audit([]) != []


def test_two_values() -> None:
    assert solve([1, 2]) == 2


def test_reverse() -> None:
    assert solve([5, 4, 3, 2, 1]) == 1


def test_mixed() -> None:
    assert solve([3, 1, 4, 1, 5, 9, 2, 6]) == 4

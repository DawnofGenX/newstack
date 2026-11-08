from __future__ import annotations

from {{ package_name }}.solve import (
    MAX_AMOUNT,
    MAX_COINS,
    MAX_DENOM,
    CoinChangeError,
    audit,
    solve,
    witness,
)


def test_zero() -> None:
    assert solve([1, 2, 5], 0) == 0


def test_exact_coin() -> None:
    assert solve([1, 2, 5], 5) == 1


def test_two_coins() -> None:
    assert solve([1, 2, 5], 6) == 2


def test_impossible() -> None:
    assert solve([2, 4], 3) == -1


def test_witness_sums() -> None:
    w = witness([1, 2, 5], 6)
    assert sum(w) == 6


def test_witness_length() -> None:
    w = witness([1, 2, 5], 6)
    assert len(w) == solve([1, 2, 5], 6)


def test_audit_clean() -> None:
    assert audit([1, 2, 5], 6) == []


def test_too_many_coins() -> None:
    import pytest

    with pytest.raises(CoinChangeError):
        solve([1] * (MAX_COINS + 1), 5)


def test_bad_amount() -> None:
    import pytest

    with pytest.raises(CoinChangeError):
        solve([1, 2], -1)


def test_empty_coins() -> None:
    import pytest

    with pytest.raises(CoinChangeError):
        solve([], 5)


def test_coin_zero() -> None:
    import pytest

    with pytest.raises(CoinChangeError):
        solve([0, 1], 5)


def test_amount_too_large() -> None:
    import pytest

    with pytest.raises(CoinChangeError):
        solve([1, 2], MAX_AMOUNT + 1)


def test_coin_too_large() -> None:
    import pytest

    with pytest.raises(CoinChangeError):
        solve([MAX_DENOM + 1], 5)


def test_amount_zero_witness() -> None:
    assert witness([1, 2, 5], 0) == []


def test_impossible_witness() -> None:
    assert witness([2, 4], 3) == []


def test_classic() -> None:
    assert solve([1, 3, 4], 6) == 2


def test_duplicate_coins_ok() -> None:
    assert solve([1, 1, 2], 4) == 2


def test_single_coin() -> None:
    assert solve([3], 9) == 3


def test_audit_impossible() -> None:
    assert audit([2, 4], 3) == []

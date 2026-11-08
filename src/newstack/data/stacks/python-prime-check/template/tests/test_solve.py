"""The prime check, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    PrimeCheckError,
    audit,
    is_prime,
    next_prime,
    prime_factors,
)


def test_is_prime_true():
    assert is_prime(17) is True


def test_is_prime_false():
    assert is_prime(1) is False
    assert is_prime(4) is False


def test_next_prime_basic():
    assert next_prime(10) == 11


def test_prime_factors_basic():
    assert prime_factors(12) == [2, 2, 3]


def test_audit_empty_for_clean():
    assert audit([2, 3, 4, 5, 10]) == []


def test_refuses_non_int():
    with pytest.raises(PrimeCheckError):
        is_prime(1.5)


def test_refuses_negative():
    with pytest.raises(PrimeCheckError):
        is_prime(-1)


def test_refuses_oversized():
    with pytest.raises(PrimeCheckError):
        is_prime(10000)


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import is_prime as ip

    assert ip(2) is True

"""The sieve, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    SieveError,
    audit,
    count_primes,
    is_prime,
    primes_up_to,
)


def test_primes_basic():
    assert primes_up_to(10) == [2, 3, 5, 7]


def test_is_prime():
    assert is_prime(7) is True
    assert is_prime(4) is False


def test_count_primes():
    assert count_primes(10) == 4


def test_audit_empty_for_clean():
    assert audit([2, 5, 10, 30]) == []


def test_refuses_too_small():
    with pytest.raises(SieveError):
        primes_up_to(1)


def test_refuses_oversized():
    with pytest.raises(SieveError):
        primes_up_to(100)


def test_refuses_non_int():
    with pytest.raises(SieveError):
        primes_up_to("a")


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import primes_up_to as p

    assert p(5) == [2, 3, 5]

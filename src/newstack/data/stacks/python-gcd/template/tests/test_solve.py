"""The gcd, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import GcdError, audit, coprime, gcd, lcm


def test_gcd_basic():
    assert gcd(12, 8) == 4
    assert gcd(7, 5) == 1
    assert gcd(9, 9) == 9


def test_lcm_basic():
    assert lcm(4, 6) == 12
    assert lcm(7, 5) == 35


def test_coprime():
    assert coprime(7, 5) is True
    assert coprime(4, 6) is False


def test_audit_empty_for_clean():
    assert audit([(2, 4), (3, 5), (10, 15)]) == []


def test_refuses_non_positive():
    with pytest.raises(GcdError):
        gcd(0, 5)
    with pytest.raises(GcdError):
        gcd(5, -1)


def test_refuses_oversized():
    with pytest.raises(GcdError):
        gcd(100, 5)


def test_refuses_non_int():
    with pytest.raises(GcdError):
        gcd("a", 5)


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import gcd as g

    assert g(6, 10) == 2

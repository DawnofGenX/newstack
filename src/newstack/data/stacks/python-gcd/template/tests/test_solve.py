"""The gcd, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    GcdError,
    audit,
    extended_gcd,
    gcd,
    mod_inverse,
)


def test_gcd_basic():
    assert gcd(4, 6) == 2
    assert gcd(0, 5) == 5


def test_extended_gcd_basic():
    g, x, y = extended_gcd(4, 6)
    assert g == 2
    assert 4 * x + 6 * y == g


def test_mod_inverse_basic():
    assert mod_inverse(3, 7) == 5


def test_audit_empty_for_clean():
    assert audit([(4, 6), (3, 5), (7, 7)]) == []


def test_refuses_non_int():
    with pytest.raises(GcdError):
        gcd(1.5, 2)


def test_refuses_negative():
    with pytest.raises(GcdError):
        gcd(-1, 2)


def test_refuses_oversized():
    with pytest.raises(GcdError):
        gcd(10000, 2)


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import gcd as G

    assert G(2, 3) == 1

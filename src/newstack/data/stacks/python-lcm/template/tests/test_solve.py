"""The lcm, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    LcmError,
    audit,
    gcd,
    is_coprime,
    lcm,
)


def test_lcm_basic():
    assert lcm(4, 6) == 12
    assert lcm(0, 5) == 0


def test_gcd_basic():
    assert gcd(4, 6) == 2


def test_is_coprime_basic():
    assert is_coprime(3, 5) is True
    assert is_coprime(4, 6) is False


def test_audit_empty_for_clean():
    assert audit([(4, 6), (3, 5), (7, 7)]) == []


def test_refuses_non_int():
    with pytest.raises(LcmError):
        lcm(1.5, 2)


def test_refuses_negative():
    with pytest.raises(LcmError):
        lcm(-1, 2)


def test_refuses_oversized():
    with pytest.raises(LcmError):
        lcm(10000, 2)


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import lcm as L

    assert L(2, 3) == 6

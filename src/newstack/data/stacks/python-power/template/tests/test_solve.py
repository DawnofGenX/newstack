"""The power, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import PowerError, audit, fast_pow, pow_mod


def test_fast_pow_basic():
    assert fast_pow(2, 10) == 1024


def test_fast_pow_zero_exp():
    assert fast_pow(3, 0) == 1


def test_pow_mod_basic():
    assert pow_mod(2, 10, 1000) == 24


def test_audit_empty_for_clean():
    assert audit([(2, 10), (3, 5), (5, 0)]) == []


def test_refuses_non_int():
    with pytest.raises(PowerError):
        fast_pow(1.5, 2)


def test_refuses_oversized():
    with pytest.raises(PowerError):
        fast_pow(2, 1001)


def test_refuses_bad_mod():
    with pytest.raises(PowerError):
        pow_mod(2, 3, 0)


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import fast_pow as F

    assert F(2, 3) == 8

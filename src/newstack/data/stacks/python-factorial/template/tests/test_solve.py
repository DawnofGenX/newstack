"""The factorial, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    FactorialError,
    audit,
    binomial,
    factorial,
)


def test_factorial_basic():
    assert factorial(5) == 120
    assert factorial(0) == 1


def test_binomial_basic():
    assert binomial(5, 2) == 10
    assert binomial(5, 0) == 1


def test_audit_empty_for_clean():
    assert audit([0, 1, 5, 10]) == []


def test_refuses_negative():
    with pytest.raises(FactorialError):
        factorial(-1)


def test_refuses_oversized():
    with pytest.raises(FactorialError):
        factorial(21)


def test_refuses_non_int():
    with pytest.raises(FactorialError):
        factorial("a")


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import factorial as f

    assert f(4) == 24

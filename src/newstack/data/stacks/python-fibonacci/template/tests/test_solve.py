"""The fibonacci, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    FibonacciError,
    audit,
    fibonacci,
    fibonacci_list,
)


def test_fibonacci_basic():
    assert fibonacci(10) == 55
    assert fibonacci(0) == 0


def test_fibonacci_list_basic():
    assert fibonacci_list(5) == [0, 1, 1, 2, 3]


def test_audit_empty_for_clean():
    assert audit([0, 1, 5, 10]) == []


def test_refuses_negative():
    with pytest.raises(FibonacciError):
        fibonacci(-1)


def test_refuses_oversized():
    with pytest.raises(FibonacciError):
        fibonacci(31)


def test_refuses_non_int():
    with pytest.raises(FibonacciError):
        fibonacci("a")


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import fibonacci as f

    assert f(4) == 3

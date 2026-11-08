"""The digit sum, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    DigitSumError,
    audit,
    digit_count,
    digit_product,
    digit_sum,
)


def test_digit_sum_basic():
    assert digit_sum(1234) == 10
    assert digit_sum(0) == 0


def test_digit_product_basic():
    assert digit_product(1234) == 24
    assert digit_product(0) == 0


def test_digit_count_basic():
    assert digit_count(1234) == 4
    assert digit_count(0) == 1


def test_audit_empty_for_clean():
    assert audit([1, 23, 456]) == []


def test_refuses_non_int():
    with pytest.raises(DigitSumError):
        digit_sum(1.5)


def test_refuses_negative():
    with pytest.raises(DigitSumError):
        digit_sum(-1)


def test_refuses_oversized():
    with pytest.raises(DigitSumError):
        digit_sum(10000)


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import digit_sum as ds

    assert ds(99) == 18

"""The armstrong check, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    ArmstrongError,
    armstrong_sum,
    audit,
    is_armstrong,
)


def test_is_armstrong_true():
    assert is_armstrong(153) is True


def test_is_armstrong_false():
    assert is_armstrong(10) is False


def test_armstrong_sum_basic():
    assert armstrong_sum(153) == 153


def test_audit_empty_for_clean():
    assert audit([153, 370, 371]) == []


def test_refuses_non_int():
    with pytest.raises(ArmstrongError):
        is_armstrong(1.5)


def test_refuses_negative():
    with pytest.raises(ArmstrongError):
        is_armstrong(-1)


def test_refuses_oversized():
    with pytest.raises(ArmstrongError):
        is_armstrong(10000)


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import is_armstrong as ia

    assert ia(0) is True

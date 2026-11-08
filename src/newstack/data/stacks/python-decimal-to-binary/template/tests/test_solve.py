"""The conversion, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    ConversionError,
    audit,
    binary_to_decimal,
    dec_to_binary,
)


def test_dec_to_binary_basic():
    assert dec_to_binary(10) == "1010"


def test_dec_to_binary_zero():
    assert dec_to_binary(0) == "0"


def test_dec_to_binary_one():
    assert dec_to_binary(1) == "1"


def test_dec_to_binary_max():
    assert dec_to_binary(1023) == "1111111111"


def test_binary_to_decimal_basic():
    assert binary_to_decimal("1010") == 10


def test_binary_to_decimal_zero():
    assert binary_to_decimal("0") == 0


def test_binary_to_decimal_leading_zeros():
    assert binary_to_decimal("0010") == 2


def test_round_trip_small():
    for n in range(0, 64):
        assert binary_to_decimal(dec_to_binary(n)) == n


def test_audit_empty_for_clean():
    assert audit([(10, "1010"), (7, "111"), (0, "0")]) == []


def test_audit_reports_mismatch():
    breaks = audit([(10, "1011")])
    assert len(breaks) == 1


def test_refuses_negative():
    with pytest.raises(ConversionError):
        dec_to_binary(-1)


def test_refuses_oversized():
    with pytest.raises(ConversionError):
        dec_to_binary(1024)


def test_refuses_malformed_binary():
    with pytest.raises(ConversionError):
        binary_to_decimal("102")


def test_refuses_empty_binary():
    with pytest.raises(ConversionError):
        binary_to_decimal("")


def test_refuses_non_int_decimal():
    with pytest.raises(ConversionError):
        dec_to_binary(1.5)


def test_refuses_non_str_binary():
    with pytest.raises(ConversionError):
        binary_to_decimal(10)


def test_audit_refuses_malformed():
    breaks = audit([(5, "102")])
    assert len(breaks) == 1


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import (
        dec_to_binary as D,
    )

    assert D(2) == "10"
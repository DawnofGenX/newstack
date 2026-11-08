"""The conversion, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    RomanError,
    audit,
    int_to_roman,
    roman_to_int,
)


def test_int_to_roman_basic():
    assert int_to_roman(1994) == "MCMXCIV"


def test_int_to_roman_one():
    assert int_to_roman(1) == "I"


def test_int_to_roman_max():
    assert int_to_roman(3999) == "MMMCMXCIX"


def test_roman_to_int_basic():
    assert roman_to_int("MCMXCIV") == 1994


def test_roman_to_int_one():
    assert roman_to_int("I") == 1


def test_round_trip_small():
    for n in range(1, 200):
        assert roman_to_int(int_to_roman(n)) == n


def test_audit_empty_for_clean():
    assert audit([(42, "XLII"), (10, "X")]) == []


def test_audit_reports_mismatch():
    breaks = audit([(10, "XI")])
    assert len(breaks) == 1


def test_refuses_zero():
    with pytest.raises(RomanError):
        int_to_roman(0)


def test_refuses_oversized():
    with pytest.raises(RomanError):
        int_to_roman(4000)


def test_refuses_malformed_roman():
    with pytest.raises(RomanError):
        roman_to_int("ABC")


def test_refuses_empty_roman():
    with pytest.raises(RomanError):
        roman_to_int("")


def test_refuses_non_int_decimal():
    with pytest.raises(RomanError):
        int_to_roman(1.5)


def test_refuses_non_str_roman():
    with pytest.raises(RomanError):
        roman_to_int(10)


def test_audit_refuses_malformed():
    breaks = audit([(5, "ABC")])
    assert len(breaks) == 1


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import (
        int_to_roman as I,
    )

    assert I(2) == "II"

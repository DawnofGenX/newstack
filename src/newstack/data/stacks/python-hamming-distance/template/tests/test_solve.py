"""The conversion, checked against the oracle and the refusal."""

from __future__ import annotations

import pytest

from {{ package_name }}.solve import (
    HammingError,
    audit,
    hamming,
    hamming_text,
)


def test_hamming_basic():
    assert hamming(7, 11) == 2


def test_hamming_zero():
    assert hamming(0, 0) == 0


def test_hamming_max():
    assert hamming(0, 1023) == 10


def test_hamming_text_basic():
    assert hamming_text("abc", "axc") == 1


def test_hamming_text_empty():
    assert hamming_text("", "") == 0


def test_audit_empty_for_clean():
    assert audit([(7, 11, 2), (0, 0, 0)]) == []


def test_audit_reports_mismatch():
    breaks = audit([(7, 11, 0)])
    assert len(breaks) == 1


def test_refuses_oversized():
    with pytest.raises(HammingError):
        hamming(1024, 0)


def test_refuses_negative():
    with pytest.raises(HammingError):
        hamming(-1, 0)


def test_refuses_length_mismatch():
    with pytest.raises(HammingError):
        hamming_text("ab", "abc")


def test_refuses_non_int():
    with pytest.raises(HammingError):
        hamming(1.5, 0)


def test_audit_refuses_malformed():
    breaks = audit([(1024, 0, 0)])
    assert len(breaks) == 1


def test_long_project_name_still_fits_line_length():
    from {{ package_name }}.solve import (
        hamming as H,
    )

    assert H(0, 0) == 0

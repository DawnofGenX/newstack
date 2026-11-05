"""Parsing is where a rounding decision gets made, so it must be visible."""

from __future__ import annotations

import pytest

from {{ package_name }} import errors as errors_mod
from {{ package_name }} import parse as subject


@pytest.mark.parametrize(
    ("text", "amount"),
    [
        ("12.34 USD", 1234),
        ("USD 12.34", 1234),
        ("1,234,567.89 USD", 123456789),
        ("1,000 USD", 100000),
        ("1200 JPY", 1200),
        ("-12.34 USD", -1234),
        ("0.05 USD", 5),
    ],
)
def test_text_parses_to_minor_units(text: str, amount: int) -> None:
    assert subject.parse(text).amount == amount


def test_a_third_decimal_is_refused_by_default() -> None:
    with pytest.raises(errors_mod.ParseError, match="more decimal places than USD"):
        subject.parse("12.345 USD")


@pytest.mark.parametrize(
    ("text", "rounding", "amount"),
    [
        ("12.345 USD", "half-up", 1235),
        ("12.345 USD", "half-even", 1234),
        ("12.349 USD", "down", 1234),
        ("12.341 USD", "up", 1235),
        ("1200.5 JPY", "half-up", 1201),
        ("1.0005 KWD", "half-even", 1000),
    ],
)
def test_a_named_rounding_mode_is_applied(text: str, rounding: str, amount: int) -> None:
    assert subject.parse(text, rounding).amount == amount


@pytest.mark.parametrize(
    "text",
    [
        "12.34",
        "",
        "USD",
        "12.34 XYZ",
        "twelve dollars",
        "12,34.5 USD",
        "12,34 USD",
        "--1 USD",
    ],
)
def test_bad_text_is_refused(text: str) -> None:
    with pytest.raises(errors_mod.ParseError):
        subject.parse(text)


def test_an_unknown_rounding_is_refused() -> None:
    with pytest.raises(errors_mod.ParseError, match="unknown rounding"):
        subject.parse("1 USD", "sideways")

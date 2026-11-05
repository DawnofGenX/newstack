"""Money is an integer and a currency code; these tests keep it that way."""

from __future__ import annotations

from decimal import Decimal

import pytest

from {{ package_name }} import errors as errors_mod
from {{ package_name }} import model as subject


def test_the_currency_table_knows_its_exponents() -> None:
    assert subject.currency_of("usd").exponent == 2
    assert subject.currency_of("JPY").scale == 1
    assert subject.currency_of("KWD").scale == 1000


def test_an_unknown_currency_is_refused() -> None:
    with pytest.raises(errors_mod.UnknownCurrency, match="unknown currency 'XYZ'"):
        subject.Money(100, "XYZ")


def test_a_float_amount_is_refused() -> None:
    with pytest.raises(TypeError, match="minor units"):
        subject.Money(12.5, "USD")


def test_a_boolean_amount_is_refused() -> None:
    with pytest.raises(TypeError):
        subject.Money(True, "USD")


def test_addition_and_subtraction_are_exact() -> None:
    total = subject.Money(1000, "USD").add(subject.Money(250, "USD"))
    assert total.amount == 1250
    assert total.subtract(subject.Money(1250, "USD")).amount == 0


def test_a_currency_mismatch_is_refused() -> None:
    with pytest.raises(errors_mod.CurrencyMismatch, match="USD with INR"):
        subject.Money(1000, "USD").add(subject.Money(100, "INR"))


def test_a_whole_multiplier_is_exact() -> None:
    assert subject.Money(1234, "USD").times(3).amount == 3702


def test_a_fractional_multiplier_rounds_half_to_even() -> None:
    assert subject.Money(5, "USD").times(Decimal("0.5")).amount == 2
    assert subject.Money(7, "USD").times(Decimal("0.5")).amount == 4


def test_a_float_multiplier_is_refused() -> None:
    with pytest.raises(TypeError, match="float"):
        subject.Money(100, "USD").times(0.5)


def test_a_percentage_rounds_once() -> None:
    assert subject.Money(999, "USD").percent(Decimal(18)).amount == 180


def test_formatting_covers_the_awkward_cases() -> None:
    assert subject.Money(1234, "USD").format() == "12.34 USD"
    assert subject.Money(1205, "USD").format() == "12.05 USD"
    assert subject.Money(123456789, "USD").format() == "1,234,567.89 USD"
    assert subject.Money(-1234, "USD").format() == "-12.34 USD"
    assert subject.Money(1200, "JPY").format() == "1,200 JPY"
    assert subject.Money(1234, "KWD").format() == "1.234 KWD"


def test_major_units_are_a_decimal() -> None:
    assert subject.Money(1234, "USD").major() == Decimal("12.34")


def test_compare_refuses_a_mismatch() -> None:
    assert subject.Money(100, "USD").compare(subject.Money(200, "USD")) == -1
    with pytest.raises(errors_mod.CurrencyMismatch):
        subject.Money(100, "USD").compare(subject.Money(200, "EUR"))


def test_money_has_no_cross_currency_ordering() -> None:
    with pytest.raises(TypeError):
        _ = subject.Money(100, "JPY") < subject.Money(1, "USD")

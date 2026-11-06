from decimal import Decimal

import pytest

from {{ package_name }}.evaluator import (
    PRECISION,
    EvalError,
    as_text,
    evaluate,
)
from {{ package_name }}.parser import parse


def value(source, **kwargs):
    return as_text(evaluate(parse(source), **kwargs))


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("2 + 3 * 4", "14"),
        ("(2 + 3) * 4", "20"),
        ("2 ^ 3 ^ 2", "512"),
        ("(2 ^ 3) ^ 2", "64"),
        ("-2 ^ 2", "-4"),
        ("(-2) ^ 2", "4"),
        ("2 ^ -1", "0.5"),
        ("1 - 2 - 3", "-4"),
        ("1 - (2 - 3)", "2"),
        ("10 % 3", "1"),
        ("1 + 2 < 4", "1"),
        ("4 < 3", "0"),
    ],
)
def test_values(source, expected):
    assert value(source) == expected


def test_a_tenth_plus_two_tenths_is_exactly_three_tenths():
    assert value("0.1 + 0.2") == "0.3"
    assert Decimal(value("0.1 + 0.2")) == Decimal("0.3")


def test_an_eighth_has_a_finite_expansion():
    assert value("1 / 8") == "0.125"


def test_a_third_is_refused_in_exact_mode():
    with pytest.raises(EvalError) as caught:
        evaluate(parse("1 / 3"))
    assert "no finite decimal expansion" in str(caught.value)


def test_a_third_is_rounded_when_asked():
    rounded = value("1 / 3", exact=False)
    assert rounded.startswith("0.3333333333333333333333333333")
    assert len(rounded.split(".")[1]) == PRECISION


@pytest.mark.parametrize("source", ["1 / 0", "5 % 0"])
def test_division_by_zero_is_refused(source):
    with pytest.raises(EvalError) as caught:
        evaluate(parse(source))
    assert "by zero" in str(caught.value)


def test_a_fractional_power_is_refused():
    with pytest.raises(EvalError):
        evaluate(parse("4 ^ 0.5"))


def test_sqrt_of_a_square_is_exact():
    assert value("sqrt(81)") == "9"
    assert value("sqrt(0.25)") == "0.5"


def test_sqrt_of_a_non_square_is_refused_exactly():
    with pytest.raises(EvalError) as caught:
        evaluate(parse("sqrt(2)"))
    assert "does not terminate" in str(caught.value)


def test_sqrt_of_a_non_square_rounds():
    assert value("sqrt(2)", exact=False).startswith("1.41421356")


def test_sqrt_of_a_negative_is_refused():
    with pytest.raises(EvalError):
        evaluate(parse("sqrt(-1)"))


def test_functions_take_the_arguments_they_take():
    assert value("max(1, 7, 3)") == "7"
    assert value("min(1, 7, 3)") == "1"
    assert value("abs(-4)") == "4"
    assert value("round(2.5)") == "3"
    assert value("round(-2.5)") == "-3"
    with pytest.raises(EvalError):
        evaluate(parse("abs(1, 2)"))


def test_an_unknown_function_is_refused():
    with pytest.raises(EvalError) as caught:
        evaluate(parse("nope(1)"))
    assert "not a function" in str(caught.value)


def test_a_name_is_taken_from_the_values():
    assert value("x * 2", values={"x": Decimal("21")}) == "42"


def test_a_missing_name_is_refused():
    with pytest.raises(EvalError) as caught:
        evaluate(parse("x + 1"))
    assert "not defined" in str(caught.value)


def test_an_error_carries_the_expression_and_the_column():
    with pytest.raises(EvalError) as caught:
        evaluate(parse("1 + 2 / 0"), text="1 + 2 / 0")
    assert "column 7" in str(caught.value)
    assert caught.value.caret().splitlines()[0] == "  1 + 2 / 0"


def test_a_large_exponent_is_refused_rather_than_computed():
    with pytest.raises(EvalError) as caught:
        evaluate(parse("2 ^ 5000"))
    assert "wait" in str(caught.value)

from __future__ import annotations

import pytest

from {{ package_name }}.calc import (
    evaluate,
    value_of,
)
from {{ package_name }}.expr import (
    ExprError,
    Number,
    Op,
)
from {{ package_name }}.yard import (
    to_postfix,
)


def queue(*tokens: object) -> list:
    return list(tokens)


def test_a_lone_number_answers_itself() -> None:
    assert evaluate(queue(Number(7))) == 7


def test_an_operator_needs_two_answers_held() -> None:
    with pytest.raises(ExprError):
        evaluate(queue(Number(1), Op("+")))


def test_a_postfix_list_leaves_one_answer() -> None:
    with pytest.raises(ExprError):
        evaluate(queue(Number(1), Number(2)))


def test_nothing_empty_is_reckoned() -> None:
    with pytest.raises(ExprError):
        evaluate([])
    with pytest.raises(ExprError):
        evaluate("1 2 +")


def test_division_floors() -> None:
    assert value_of("6 / 4") == 1
    assert value_of("7 / 2") == 3


def test_a_divided_zero_raises() -> None:
    with pytest.raises(ExprError):
        value_of("5 / 0")


def test_the_documented_precedence_answers() -> None:
    assert value_of("2 + 3 * 4") == 14
    assert value_of("( 2 + 3 ) * 4") == 20


def test_every_operator_binds_left() -> None:
    assert value_of("100 - 20 - 5") == 75
    assert value_of("100 / 5 / 2") == 10


def test_evaluate_of_the_yield_is_value_of() -> None:
    for expr in ("7", "1 + 2", "2 + 3 * 4", "3 + 4 * 2 / ( 1 - 5 ) * 2"):
        assert evaluate(to_postfix(expr)) == value_of(expr)

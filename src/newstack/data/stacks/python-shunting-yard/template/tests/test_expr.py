from __future__ import annotations

import pytest

from {{ package_name }}.expr import (
    CLOSE,
    MAX_EXPR,
    OPEN,
    ExprError,
    Number,
    Op,
    read_expr,
    token_text,
)


def test_a_number_reads_whole() -> None:
    assert read_expr("7") == [Number(7)]


def test_spaces_are_free() -> None:
    assert read_expr(" 1 + 2 ") == read_expr("1+2")


def test_parentheses_arrive_as_tokens() -> None:
    assert read_expr("(1)") == [OPEN, Number(1), CLOSE]


def test_operators_carry_the_documented_precedence() -> None:
    assert Op("*").precedence > Op("+").precedence
    assert Op("/").precedence > Op("-").precedence
    assert all(Op(symbol).left_associative for symbol in "+-*/")


@pytest.mark.parametrize("noise", ["a + 1", "1.5 + 1", "07 + 1", "2 % 3", "1 & 2"])
def test_noise_is_refused(noise: str) -> None:
    with pytest.raises(ExprError):
        read_expr(noise)


def test_the_empty_expression_answers_nothing() -> None:
    with pytest.raises(ExprError):
        read_expr("")
    with pytest.raises(ExprError):
        read_expr("   ")


def test_a_non_string_is_no_expression() -> None:
    with pytest.raises(ExprError):
        read_expr(7)


def test_the_ceiling_binds() -> None:
    with pytest.raises(ExprError):
        read_expr("1" * (MAX_EXPR + 1))


def test_the_character_face_round_trips() -> None:
    assert token_text(Number(42)) == "42"
    assert token_text(Op("*")) == "*"
    assert token_text(OPEN) == "("

from decimal import Decimal

import pytest

from {{ package_name }}.lexer import (
    NAME,
    NUMBER,
    LexError,
    Token,
    tokenize,
)


def kinds(text):
    return [token.kind for token in tokenize(text)]


def test_tokenize_ends_with_an_end_token():
    tokens = tokenize("1")
    assert tokens[-1].kind == "end"
    assert tokens[-1].start == 1


def test_numbers_keep_their_value_and_text():
    token = tokenize("4.50")[0]
    assert token.kind == NUMBER
    assert token.text == "4.50"
    assert token.value == Decimal("4.50")


def test_an_exponent_is_part_of_the_number():
    assert tokenize("4.5e2")[0].value == Decimal("450.0")
    assert tokenize("1e-3")[0].value == Decimal("0.001")


def test_names_are_letters_digits_and_underscores():
    assert tokenize("_x1")[0].kind == NAME
    assert tokenize("_x1")[0].text == "_x1"


def test_two_character_operators_are_one_token():
    tokens = tokenize("a<=b")
    assert tokens[1].text == "<="
    assert len(tokens) == 4


def test_columns_are_one_based():
    assert tokenize("  7")[0].column == 3


def test_whitespace_is_skipped():
    assert kinds(" 1 + 2 ") == [NUMBER, "operator", NUMBER, "end"]


@pytest.mark.parametrize("source", ["2 $ 3", "1 & 2", "3 ~ 4"])
def test_a_stray_character_names_its_column(source):
    with pytest.raises(LexError) as caught:
        tokenize(source)
    assert "not a token" in str(caught.value)
    assert "column 3" in str(caught.value)


@pytest.mark.parametrize("source", ["1.", "1e", "2.5e+"])
def test_a_number_that_stops_early_is_refused(source):
    with pytest.raises(LexError):
        tokenize(source)


def test_the_error_object_keeps_the_position():
    with pytest.raises(LexError) as caught:
        tokenize("2 $ 3")
    assert caught.value.position == 2


def test_a_token_prints_its_column():
    token = Token(NUMBER, "7", 4)
    assert "column 5" in str(token)

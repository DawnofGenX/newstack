"""Turning text into tokens that remember where they came from.

Every token carries the offset it started at, so an error can say which column
it is about instead of which character it disliked. A parser that cannot point
at a column turns a typo into a mystery.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

NUMBER = "number"
NAME = "name"
OPERATOR = "operator"
LPAREN = "("
RPAREN = ")"
COMMA = ","

TWO_CHAR = ("<=", ">=", "==", "!=")
ONE_CHAR = ("+", "-", "*", "/", "%", "^", "<", ">")


class LexError(ValueError):
    """Text that is not made of tokens this language has."""

    def __init__(self, message: str, position: int) -> None:
        super().__init__(f"{message} at column {position + 1}")
        self.message = message
        self.position = position


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    start: int
    value: object = None

    @property
    def column(self) -> int:
        return self.start + 1

    @property
    def end(self) -> int:
        return self.start + len(self.text)

    def __str__(self) -> str:
        return f"{self.kind} {self.text!r} at column {self.column}"


def _is_digit(char: str) -> bool:
    return "0" <= char <= "9"


def _is_name_start(char: str) -> bool:
    return char.isascii() and (char.isalpha() or char == "_")


def _is_name_char(char: str) -> bool:
    return _is_name_start(char) or _is_digit(char)


def _read_number(text: str, start: int) -> tuple[str, int]:
    index = start
    seen_dot = False
    seen_exponent = False
    while index < len(text):
        char = text[index]
        if _is_digit(char):
            index += 1
        elif char == "." and not seen_dot and not seen_exponent:
            seen_dot = True
            index += 1
        elif char in "eE" and not seen_exponent:
            seen_exponent = True
            index += 1
            if index < len(text) and text[index] in "+-":
                index += 1
        else:
            break
    return text[start:index], index


def _value_of(literal: str, position: int) -> Decimal:
    try:
        return Decimal(literal)
    except InvalidOperation:  # pragma: no cover - the reader only feeds it digits
        raise LexError(f"{literal!r} is not a number", position) from None


def tokenize(text: str) -> list[Token]:
    """Split ``text`` into tokens, ending with one END token at the last offset."""
    tokens: list[Token] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in " \t\n\r":
            index += 1
            continue
        if _is_digit(char):
            literal, end = _read_number(text, index)
            if literal.endswith((".", "e", "E", "e+", "e-", "E+", "E-")):
                raise LexError(f"the number {literal!r} has no digits after {literal[-1]!r}", index)
            tokens.append(Token(NUMBER, literal, index, _value_of(literal, index)))
            index = end
            continue
        if _is_name_start(char):
            end = index + 1
            while end < len(text) and _is_name_char(text[end]):
                end += 1
            word = text[index:end]
            tokens.append(Token(NAME, word, index, word))
            index = end
            continue
        pair = text[index : index + 2]
        if pair in TWO_CHAR:
            tokens.append(Token(OPERATOR, pair, index))
            index += 2
            continue
        if char in ONE_CHAR:
            tokens.append(Token(OPERATOR, char, index))
            index += 1
            continue
        if char == "(":
            tokens.append(Token(LPAREN, char, index))
            index += 1
            continue
        if char == ")":
            tokens.append(Token(RPAREN, char, index))
            index += 1
            continue
        if char == ",":
            tokens.append(Token(COMMA, char, index))
            index += 1
            continue
        raise LexError(f"{char!r} is not a token in this language", index)
    tokens.append(Token("end", "", len(text)))
    return tokens

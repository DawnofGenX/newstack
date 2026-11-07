"""The gate every expression passes before the yard looks at it.

An expression is nonneg integers, ``+ - * /``, and parentheses over
a bounded run of characters: no floats, no letters, no leading
zeros, no power, no modulo. Numbers are read whole, operators one
character at a time, and every parenthesis must close. The gate
answers loud input with ExprError and quiet input with its tokens.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_EXPR = 10_000
MAX_NUMBER = 1_000_000_000
OPERATORS = "+-*/"
LEFT_PRECEDENCE = 1
TIGHT_PRECEDENCE = 2

OPEN = "("
CLOSE = ")"


class ExprError(ValueError):
    """The expression is not one this yard can read."""

    __slots__ = ()


@dataclass(frozen=True)
class Number:
    """One nonneg integer, read whole by the gate."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise ExprError(f"{self.value!r} is no integer")
        if self.value < 0:
            raise ExprError(f"{self.value} is negative, the yard eats nonneg integers")
        if self.value > MAX_NUMBER:
            raise ExprError(f"{self.value} is past the {MAX_NUMBER} ceiling")


@dataclass(frozen=True)
class Op:
    """One operator, carrying the precedence and binding it obeys."""

    symbol: str

    def __post_init__(self) -> None:
        if self.symbol not in OPERATORS:
            raise ExprError(f"{self.symbol!r} is no operator the yard knows")

    @property
    def precedence(self) -> int:
        """Tighter binding answers the higher number."""
        return TIGHT_PRECEDENCE if self.symbol in "*/" else LEFT_PRECEDENCE

    @property
    def left_associative(self) -> bool:
        """Every operator the yard eats binds left to right."""
        return True


def read_expr(expr: object) -> list:
    """Return the token list, or refuse naming what broke.

    Numbers arrive as Number, operators as Op, parentheses as the
    bare characters the yard counts itself.
    """
    if not isinstance(expr, str):
        raise ExprError(f"{expr!r} is not a string, so it is no expression")
    if len(expr) > MAX_EXPR:
        raise ExprError(f"an expression runs to {MAX_EXPR} characters, this runs longer")
    tokens: list = []
    depth = 0
    index = 0
    while index < len(expr):
        ch = expr[index]
        if ch in " \t":
            index += 1
            continue
        if ch.isdigit():
            end = index
            while end < len(expr) and expr[end].isdigit():
                end += 1
            digits = expr[index:end]
            if len(digits) > 1 and digits[0] == "0":
                raise ExprError(f"{digits} has a leading zero, numbers arrive plain")
            tokens.append(Number(int(digits)))
            index = end
            continue
        if ch in OPERATORS:
            tokens.append(Op(ch))
            index += 1
            continue
        if ch == OPEN:
            depth += 1
            tokens.append(OPEN)
            index += 1
            continue
        if ch == CLOSE:
            depth -= 1
            if depth < 0:
                raise ExprError("a ) opens nothing, the parenthesis is unbalanced")
            tokens.append(CLOSE)
            index += 1
            continue
        raise ExprError(f"{expr!r} holds {ch!r}, which the yard does not eat")
    if depth:
        raise ExprError("a ( never closed, the parenthesis is unbalanced")
    if not tokens:
        raise ExprError("the empty expression answers nothing")
    return tokens


def token_text(token: object) -> str:
    """The character face of one token, for transcripts and fixtures."""
    if isinstance(token, Number):
        return str(token.value)
    if isinstance(token, Op):
        return token.symbol
    if token in (OPEN, CLOSE):
        return str(token)
    raise ExprError(f"{token!r} is no token the yard ships")

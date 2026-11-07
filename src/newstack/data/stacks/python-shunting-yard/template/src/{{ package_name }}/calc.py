"""The reckoning: postfix tokens in, one integer out.

evaluate(tokens) walks a postfix list the yard or the oracle
handed over, keeps a stack of results, and answers the single
integer left standing. '/' is floor division: 6 / 4 is 1, and a
division by zero raises ExprError naming the divisor.
value_of(expr) is the whole promise in one call - to_postfix then
evaluate - and it answers exactly what the shipped recursive
descent oracle answers, on every shipped and seeded corpus.
"""

from __future__ import annotations

from .expr import CLOSE, OPEN, ExprError, Number, Op
from .yard import to_postfix


def evaluate(tokens: object) -> int:
    """Walk a postfix token list and answer the integer it means."""
    if not isinstance(tokens, list) or not tokens:
        raise ExprError("the yard answers a token list, nothing else")
    stack: list = []
    for token in tokens:
        if isinstance(token, Number):
            stack.append(token.value)
            continue
        if isinstance(token, Op):
            if len(stack) < 2:
                raise ExprError("an operator waits with fewer than two answers held")
            right = stack.pop()
            left = stack.pop()
            stack.append(_apply(token.symbol, left, right))
            continue
        if token in (OPEN, CLOSE):
            raise ExprError("a parenthesis sits in a postfix list")
        raise ExprError(f"{token!r} is no token the yard ships")
    if len(stack) != 1:
        raise ExprError("the postfix list leaves more than one answer standing")
    return int(stack[0])


def value_of(expr: object) -> int:
    """The whole promise: the yard converts, the reckoning answers."""
    return evaluate(to_postfix(expr))


def _apply(symbol: str, left: int, right: int) -> int:
    """One arithmetic step; '/' floors toward minus infinity."""
    if symbol == "+":
        return left + right
    if symbol == "-":
        return left - right
    if symbol == "*":
        return left * right
    if right == 0:
        raise ExprError("a division by zero answers nothing")
    return left // right

"""The oracle: a recursive descent that parses and answers another way.

The oracle is deliberately slow and deliberately complete. It
skips the yard entirely - read_expr hands it tokens, and a
descending reader eats the grammar in its own order: sum over
product over atom, atom being a number or a bracketed sum. Where
the yard parks operators on a stack, the oracle recurses. Where
the yard checks precedence on a pop, the oracle checks it in the
call structure. Every answer the oracle gives, value_of gives
too - that equality is the product, audited per corpus.
"""

from __future__ import annotations

from .expr import CLOSE, OPEN, ExprError, Number, Op


def descent(expr: object) -> int:
    """Parse and answer by descending, never by shunting."""
    reader = _Reader(expr)
    answer = reader.sum()
    reader.finish()
    return answer


class _Reader:
    """The descending reader: sum, then product, then atom."""

    __slots__ = ("_at", "_tokens")

    def __init__(self, expr: object) -> None:
        if isinstance(expr, list):
            self._tokens = list(expr)
        else:
            self._tokens = read_infix(expr)
        self._at = 0

    def finish(self) -> None:
        if self._at != len(self._tokens):
            raise ExprError("the expression ends with answers still parked")

    def sum(self) -> int:
        answer = self.product()
        while self._holding_op(("+", "-")):
            symbol = self._take_op().symbol
            right = self.product()
            answer = _step(symbol, answer, right)
        return answer

    def product(self) -> int:
        answer = self.atom()
        while self._holding_op(("*", "/")):
            symbol = self._take_op().symbol
            right = self.atom()
            answer = _step(symbol, answer, right)
        return answer

    def atom(self) -> int:
        if self._at >= len(self._tokens):
            raise ExprError("the expression stops while a number is owed")
        token = self._tokens[self._at]
        if isinstance(token, Number):
            self._at += 1
            return token.value
        if token == OPEN:
            self._at += 1
            answer = self.sum()
            if self._at >= len(self._tokens) or self._tokens[self._at] != CLOSE:
                raise ExprError("a ( never closed, the parenthesis is unbalanced")
            self._at += 1
            return answer
        raise ExprError("an atom waits for a number or a (")

    def _holding_op(self, symbols: tuple) -> bool:
        return (
            self._at < len(self._tokens)
            and isinstance(self._tokens[self._at], Op)
            and self._tokens[self._at].symbol in symbols
        )

    def _take_op(self) -> Op:
        token = self._tokens[self._at]
        self._at += 1
        return token


def read_infix(expr: object) -> list:
    """Tokenize through the gate, kept local to dodge the import cycle."""
    from .expr import read_expr

    return read_expr(expr)


def _step(symbol: str, left: int, right: int) -> int:
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

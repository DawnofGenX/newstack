"""Evaluating the tree exactly, or rounding at a stated precision.

Exact mode works in ``Fraction``, so it can tell the difference between a value
that has a finite decimal expansion (``1 / 8`` is ``0.125``) and one that does
not (``1 / 3``). Rounded mode works in ``Decimal`` and says how many digits it
kept. A calculator that hides which of the two it did is a calculator you
cannot check.
"""

from __future__ import annotations

import math
from decimal import (
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    localcontext,
)
from fractions import Fraction

from .nodes import COMPARISONS, Binary, Call, Name, Node, Number, Unary, format_number

PRECISION = 28
ROUNDING = ROUND_HALF_EVEN

FUNCTIONS = ("abs", "max", "min", "round", "sqrt")


class EvalError(ValueError):
    """An expression that parses but has no answer of the kind asked for."""

    def __init__(self, message: str, position: int = 0, text: str = "") -> None:
        super().__init__(f"{message} at column {position + 1}")
        self.message = message
        self.position = position
        self.text = text

    def caret(self) -> str:
        if not self.text:
            return ""
        return f"  {self.text}\n  {' ' * self.position}^"


def _terminates(value: Fraction) -> bool:
    denominator = value.denominator
    for prime in (2, 5):
        while denominator % prime == 0:
            denominator //= prime
    return denominator == 1


def _to_decimal(value: Fraction) -> Decimal:
    with localcontext() as context:
        context.prec = 400
        return Decimal(value.numerator) / Decimal(value.denominator)


class Exact:
    """Arithmetic in the rationals, so 'exact' means exact."""

    exact = True

    def number(self, value: Decimal) -> Fraction:
        return Fraction(value)

    def unary(self, op: str, value: Fraction) -> Fraction:
        return -value if op == "-" else value

    def binary(self, op: str, left: Fraction, right: Fraction, node: Binary) -> Fraction:
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op in ("/", "%") and right == 0:
            raise EvalError(f"{'division' if op == '/' else 'remainder'} by zero", node.start)
        if op == "/":
            return left / right
        if op == "%":
            quotient = left / right
            whole = int(quotient)
            return left - whole * right
        exponent = right
        if exponent.denominator != 1:
            raise EvalError(
                f"{format_number(Decimal(exponent.numerator))}/"
                f"{exponent.denominator} is a fractional power, and exact mode has no "
                "answer of that kind; use sqrt() or --inexact",
                node.start,
            )
        if exponent.numerator > 4_000:
            raise EvalError("an exponent above 4000 is not a calculation, it is a wait", node.start)
        if exponent < 0 and left == 0:
            raise EvalError("0 raised to a negative power divides by zero", node.start)
        return left**exponent.numerator

    def compare(self, op: str, left: Fraction, right: Fraction) -> Fraction:
        return Fraction(int(_compare(op, left, right)))

    def call(self, name: str, args: list[Fraction], node: Call) -> Fraction:
        if name == "abs":
            _arity(name, args, 1, node)
            return abs(args[0])
        if name in ("min", "max"):
            if len(args) < 1:
                raise EvalError(f"{name}() needs at least one argument", node.start)
            return (min if name == "min" else max)(args)
        if name == "round":
            _arity(name, args, 1, node)
            return _round_half_away(args[0], node)
        if name == "sqrt":
            _arity(name, args, 1, node)
            if args[0] < 0:
                raise EvalError("sqrt() of a negative number has no real answer", node.start)
            numerator, denominator = args[0].numerator, args[0].denominator
            root_numerator, root_denominator = math.isqrt(numerator), math.isqrt(denominator)
            if root_numerator**2 != numerator or root_denominator**2 != denominator:
                raise EvalError(
                    f"sqrt({format_number(_to_decimal(args[0]))}) does not terminate in "
                    "decimal digits; pass --inexact to round it",
                    node.start,
                )
            return Fraction(root_numerator, root_denominator)
        raise EvalError(f"{name!r} is not a function this language has", node.start)


class Rounded:
    """Arithmetic in decimal, rounded to a precision the caller is told about."""

    exact = False

    def number(self, value: Decimal) -> Decimal:
        return value

    def unary(self, op: str, value: Decimal) -> Decimal:
        return -value if op == "-" else value

    def binary(self, op: str, left: Decimal, right: Decimal, node: Binary) -> Decimal:
        if op in ("/", "%") and right == 0:
            raise EvalError(f"{'division' if op == '/' else 'remainder'} by zero", node.start)
        with localcontext() as context:
            context.prec = PRECISION
            context.rounding = ROUNDING
            try:
                if op == "+":
                    return left + right
                if op == "-":
                    return left - right
                if op == "*":
                    return left * right
                if op == "/":
                    return left / right
                if op == "%":
                    return left % right
                if right != right.to_integral_value():
                    raise EvalError(
                        f"a fractional exponent ({right}) is not a power this language takes",
                        node.start,
                    )
                return left ** int(right)
            except (DivisionByZero, InvalidOperation) as error:
                raise EvalError(f"{op} is not defined here: {error}", node.start) from None

    def compare(self, op: str, left: Decimal, right: Decimal) -> Decimal:
        return Decimal(int(_compare(op, left, right)))

    def call(self, name: str, args: list[Decimal], node: Call) -> Decimal:
        if name == "abs":
            _arity(name, args, 1, node)
            return abs(args[0])
        if name in ("min", "max"):
            if len(args) < 1:
                raise EvalError(f"{name}() needs at least one argument", node.start)
            return (min if name == "min" else max)(args)
        if name == "round":
            _arity(name, args, 1, node)
            return _round_half_away(args[0], node)
        if name == "sqrt":
            _arity(name, args, 1, node)
            if args[0] < 0:
                raise EvalError("sqrt() of a negative number has no real answer", node.start)
            with localcontext() as context:
                context.prec = PRECISION
                return args[0].sqrt()
        raise EvalError(f"{name!r} is not a function this language has", node.start)


def _arity(name: str, args: list, wanted: int, node: Call) -> None:
    if len(args) != wanted:
        raise EvalError(f"{name}() takes {wanted} argument(s), not {len(args)}", node.start)


def _compare(op: str, left, right) -> bool:
    if op == "<":
        return left < right
    if op == "<=":
        return left <= right
    if op == ">":
        return left > right
    if op == ">=":
        return left >= right
    if op == "==":
        return left == right
    return left != right


def _round_half_away(value, node: Node):
    if isinstance(value, Fraction):
        whole = int(value)
        remainder = value - whole
        if remainder >= Fraction(1, 2):
            return Fraction(whole + 1)
        if remainder <= Fraction(-1, 2):
            return Fraction(whole - 1)
        return Fraction(whole)
    with localcontext() as context:
        context.prec = PRECISION
        return value.quantize(Decimal(1), rounding=ROUND_HALF_UP)


def _walk(node: Node, engine) -> object:
    if isinstance(node, Number):
        return engine.number(node.value)
    if isinstance(node, Name):
        raise EvalError(f"{node.identifier!r} is not defined", node.start)
    if isinstance(node, Unary):
        return engine.unary(node.op, _walk(node.operand, engine))
    if isinstance(node, Call):
        return engine.call(node.name, [_walk(arg, engine) for arg in node.args], node)
    left, right = _walk(node.left, engine), _walk(node.right, engine)
    if node.op in COMPARISONS:
        return engine.compare(node.op, left, right)
    return engine.binary(node.op, left, right, node)


def resolve(node: Node, values: dict[str, Decimal] | None) -> Node:
    """Replace names with the numbers the caller supplied."""
    if isinstance(node, Name):
        if values is None or node.identifier not in values:
            raise EvalError(f"{node.identifier!r} is not defined", node.start)
        return Number(values[node.identifier], start=node.start)
    if isinstance(node, Unary):
        return Unary(node.op, resolve(node.operand, values), start=node.start)
    if isinstance(node, Binary):
        return Binary(node.op, resolve(node.left, values), resolve(node.right, values), node.start)
    if isinstance(node, Call):
        return Call(node.name, tuple(resolve(arg, values) for arg in node.args), start=node.start)
    return node


def evaluate(
    node: Node, *, values: dict[str, Decimal] | None = None, exact: bool = True, text: str = ""
) -> Decimal:
    """Evaluate ``node``; in exact mode refuse answers that need rounding."""
    try:
        tree = resolve(node, values)
        if not exact:
            return _walk(tree, Rounded())
        result = _walk(tree, Exact())
        if not _terminates(result):
            raise EvalError(
                f"{tree.render()} is {result.numerator}/{result.denominator}, which has no "
                f"finite decimal expansion; pass --inexact to round it to {PRECISION} digits",
                node.start,
            )
        return _to_decimal(result)
    except EvalError as error:
        error.text = text or error.text
        raise


def as_text(value: Decimal) -> str:
    return format_number(value)

"""The shunting yard: infix tokens in, postfix tokens out.

to_postfix(expr) runs Dijkstra's yard - output queued left to
right, operators parked on a stack, and the rule is short:
the operator stack yields only to tighter binding. * and / park
tighter than + and -; every operator pops what it ties or beats
before it parks, and nothing leaves a parenthesis until it
closes. The precedence is documented in expr.py. The yard is the
product: to_postfix(expr) followed by evaluate answers exactly
what value_of(expr) answers.
"""

from __future__ import annotations

from .expr import (
    CLOSE,
    OPEN,
    ExprError,
    Number,
    Op,
    read_expr,
)


def to_postfix(expr: object) -> list:
    """Infix in, postfix token list out, refusal naming what broke."""
    stack: list = []
    output: list = []
    expect_operand = True
    for token in read_expr(expr):
        if isinstance(token, Number):
            if not expect_operand:
                raise ExprError("two numbers in a row answer nothing")
            output.append(token)
            expect_operand = False
            continue
        if isinstance(token, Op):
            if expect_operand:
                raise ExprError("an operator waits for a number before it")
            while stack and isinstance(stack[-1], Op):
                parked: Op = stack[-1]
                if parked.precedence >= token.precedence:
                    output.append(stack.pop())
                else:
                    break
            stack.append(token)
            expect_operand = True
            continue
        if token == OPEN:
            if not expect_operand:
                raise ExprError("a ( sits after a number, the expression is malformed")
            stack.append(token)
            continue
        if token == CLOSE:
            while stack and stack[-1] != OPEN:
                output.append(stack.pop())
            if not stack:
                raise ExprError("a ) closes nothing the yard still holds open")
            stack.pop()
            expect_operand = False
            continue
        raise ExprError(f"{token!r} is no token the yard eats")
    if expect_operand:
        raise ExprError("the expression stops while a number is owed")
    while stack:
        tail = stack.pop()
        if tail == OPEN:
            raise ExprError("a ( never closed, the parenthesis is unbalanced")
        output.append(tail)
    return output


def postfix_text(tokens: list) -> str:
    """The postfix list's character face, single-spaced."""
    from .expr import token_text

    try:
        return " ".join(token_text(token) for token in tokens)
    except ExprError:
        raise ExprError("the yard answers only its own tokens") from None


def balanced(tokens: object) -> bool:
    """True when a token list's parentheses close, cheaply."""
    if not isinstance(tokens, list):
        return False
    depth = 0
    for token in tokens:
        if token == OPEN:
            depth += 1
        elif token == CLOSE:
            depth -= 1
            if depth < 0:
                return False
    return depth == 0

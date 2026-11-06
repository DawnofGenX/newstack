"""Precedence climbing over the tokens, with every refusal naming a column.

The grammar, in one place:

    expression    := comparison
    comparison    := additive [ ("<"|"<="|">"|">="|"=="|"!=") additive ]
    additive      := multiplicative (("+"|"-") multiplicative)*
    multiplicative:= unary (("*"|"/"|"%") unary)*
    unary         := ("-"|"+") unary | power
    power         := primary ["^" unary]
    primary       := NUMBER | NAME | NAME "(" args ")" | "(" expression ")"

Two refusals are decisions rather than omissions: comparisons do not chain
(``a < b < c`` is ambiguous between Python's meaning and C's), and a call with
no arguments is not a call.
"""

from __future__ import annotations

from .lexer import COMMA, LPAREN, NAME, NUMBER, RPAREN, Token, tokenize
from .nodes import ADDITIVE, COMPARISONS, MULTIPLICATIVE, Binary, Call, Name, Node, Number, Unary

ADDITIVE_OPS = frozenset({"+", "-"})
MULTIPLICATIVE_OPS = frozenset({"*", "/", "%"})


class ParseError(ValueError):
    """Text that is made of tokens but not of expressions."""

    def __init__(self, message: str, position: int, text: str = "") -> None:
        super().__init__(f"{message} at column {position + 1}")
        self.message = message
        self.position = position
        self.text = text

    def caret(self) -> str:
        """The line, and a caret under the column the error is about."""
        if not self.text:
            return ""
        return f"  {self.text}\n  {' ' * self.position}^"


def _found(token: Token) -> str:
    if token.kind == "end":
        return "the end of the input"
    return repr(token.text)


class Parser:
    def __init__(self, tokens: list[Token], text: str = "") -> None:
        self._tokens = tokens
        self._text = text
        self._index = 0

    def peek(self) -> Token:
        return self._tokens[self._index]

    def advance(self) -> Token:
        token = self._tokens[self._index]
        if token.kind != "end":
            self._index += 1
        return token

    def error(self, message: str, token: Token) -> ParseError:
        return ParseError(message, token.start, self._text)

    def parse(self) -> Node:
        node = self.comparison()
        token = self.peek()
        if token.kind != "end":
            raise self.error(f"{_found(token)} comes after a complete expression", token)
        return node

    def comparison(self) -> Node:
        node = self.additive()
        token = self.peek()
        if token.kind == "operator" and token.text in COMPARISONS:
            self.advance()
            right = self.additive()
            node = Binary(token.text, node, right, start=token.start)
            again = self.peek()
            if again.kind == "operator" and again.text in COMPARISONS:
                raise self.error(
                    f"{again.text!r} would chain a second comparison; "
                    "this language compares two values in one step",
                    again,
                )
        return node

    def additive(self) -> Node:
        node = self.multiplicative()
        while True:
            token = self.peek()
            if token.kind != "operator" or token.text not in ADDITIVE_OPS:
                return node
            self.advance()
            node = Binary(token.text, node, self.multiplicative(), start=token.start)

    def multiplicative(self) -> Node:
        node = self.unary()
        while True:
            token = self.peek()
            if token.kind != "operator" or token.text not in MULTIPLICATIVE_OPS:
                return node
            self.advance()
            node = Binary(token.text, node, self.unary(), start=token.start)

    def unary(self) -> Node:
        token = self.peek()
        if token.kind == "operator" and token.text in ("+", "-"):
            self.advance()
            return Unary(token.text, self.unary(), start=token.start)
        return self.power()

    def power(self) -> Node:
        node = self.primary()
        token = self.peek()
        if token.kind == "operator" and token.text == "^":
            self.advance()
            return Binary("^", node, self.unary(), start=token.start)
        return node

    def primary(self) -> Node:
        token = self.peek()
        if token.kind == NUMBER:
            self.advance()
            return Number(token.value, start=token.start)
        if token.kind == NAME:
            self.advance()
            if self.peek().kind == LPAREN:
                return self.call(token)
            return Name(token.text, start=token.start)
        if token.kind == LPAREN:
            self.advance()
            node = self.comparison()
            closing = self.peek()
            if closing.kind != RPAREN:
                raise self.error(
                    f"expected ')' to close the group opened at column {token.column}, "
                    f"found {_found(closing)}",
                    closing,
                )
            self.advance()
            return node
        raise self.error(f"expected a number, a name or '(' here, found {_found(token)}", token)

    def call(self, name_token: Token) -> Node:
        self.advance()
        if self.peek().kind == RPAREN:
            raise self.error(
                f"{name_token.text}() has no arguments, and a call with none "
                "is not a call in this language",
                self.peek(),
            )
        args = [self.comparison()]
        while self.peek().kind == COMMA:
            self.advance()
            args.append(self.comparison())
        closing = self.peek()
        if closing.kind != RPAREN:
            raise self.error(
                f"expected ')' to close the call to {name_token.text} "
                f"opened at column {name_token.column}, found {_found(closing)}",
                closing,
            )
        self.advance()
        return Call(name_token.text, tuple(args), start=name_token.start)


def parse(text: str) -> Node:
    return Parser(tokenize(text), text).parse()


def precedence_table() -> list[tuple[str, int]]:
    """The table the parser actually walks, as printed by ``explain``."""
    rows = [("unary + -", 4), ("^", 5)]
    rows.extend((op, ADDITIVE) for op in sorted(ADDITIVE_OPS))
    rows.extend((op, MULTIPLICATIVE) for op in sorted(MULTIPLICATIVE_OPS))
    rows.extend((op, 1) for op in sorted(COMPARISONS))
    rows.sort(key=lambda row: row[1])
    return rows

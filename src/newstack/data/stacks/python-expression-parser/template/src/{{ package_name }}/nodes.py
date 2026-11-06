"""The tree, and the one string that prints it back exactly.

``render`` is the inverse of parsing: ``parse(render(tree))`` is the same tree,
and the printed form carries a parenthesis only where removing it would change
the tree. That is not decoration -- it is how the parser's precedence table is
tested without trusting the table.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

ATOM = 6
UNARY_PRECEDENCE = 4
POWER = 5
MULTIPLICATIVE = 3
ADDITIVE = 2
COMPARISON = 1

PRECEDENCE = {
    "<": COMPARISON,
    "<=": COMPARISON,
    ">": COMPARISON,
    ">=": COMPARISON,
    "==": COMPARISON,
    "!=": COMPARISON,
    "+": ADDITIVE,
    "-": ADDITIVE,
    "*": MULTIPLICATIVE,
    "/": MULTIPLICATIVE,
    "%": MULTIPLICATIVE,
    "^": POWER,
}

RIGHT_ASSOCIATIVE = frozenset({"^"})
COMPARISONS = frozenset({"<", "<=", ">", ">=", "==", "!="})
NAMES_OF_PRECEDENCE = {
    ATOM: "atom",
    POWER: "power",
    UNARY_PRECEDENCE: "unary",
    MULTIPLICATIVE: "multiplicative",
    ADDITIVE: "additive",
    COMPARISON: "comparison",
}


@dataclass(frozen=True)
class Node:
    """Base class: every node knows its precedence and how to print itself."""

    @property
    def precedence(self) -> int:
        raise NotImplementedError

    @property
    def level(self) -> str:
        return NAMES_OF_PRECEDENCE[self.precedence]

    def render(self, minimum: int = 0) -> str:
        body = self.text()
        return f"({body})" if self.precedence < minimum else body

    def text(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class Number(Node):
    value: Decimal
    start: int = field(default=0, compare=False)

    @property
    def precedence(self) -> int:
        return ATOM

    def text(self) -> str:
        return format_number(self.value)


@dataclass(frozen=True)
class Name(Node):
    identifier: str
    start: int = field(default=0, compare=False)

    @property
    def precedence(self) -> int:
        return ATOM

    def text(self) -> str:
        return self.identifier


@dataclass(frozen=True)
class Unary(Node):
    op: str
    operand: Node
    start: int = field(default=0, compare=False)

    @property
    def precedence(self) -> int:
        return UNARY_PRECEDENCE

    def text(self) -> str:
        return f"{self.op}{self.operand.render(UNARY_PRECEDENCE)}"


@dataclass(frozen=True)
class Binary(Node):
    op: str
    left: Node
    right: Node
    start: int = field(default=0, compare=False)

    @property
    def precedence(self) -> int:
        return PRECEDENCE[self.op]

    def text(self) -> str:
        precedence = self.precedence
        if self.op in RIGHT_ASSOCIATIVE:
            left = self.left.render(precedence + 1)
            right = self.right.render(precedence)
        else:
            left = self.left.render(precedence)
            right = self.right.render(precedence + 1)
        return f"{left} {self.op} {right}"


@dataclass(frozen=True)
class Call(Node):
    name: str
    args: tuple[Node, ...]
    start: int = field(default=0, compare=False)

    @property
    def precedence(self) -> int:
        return ATOM

    def text(self) -> str:
        inside = ", ".join(arg.render() for arg in self.args)
        return f"{self.name}({inside})"


def format_number(value: Decimal) -> str:
    """Print a decimal without an exponent and without trailing zeros."""
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("", "-0"):
        return "0"
    return text


def walk(node: Node):
    """Yield every node, parents before children."""
    yield node
    if isinstance(node, Unary):
        yield from walk(node.operand)
    elif isinstance(node, Binary):
        yield from walk(node.left)
        yield from walk(node.right)
    elif isinstance(node, Call):
        for arg in node.args:
            yield from walk(arg)


def depth(node: Node) -> int:
    if isinstance(node, Unary):
        return 1 + depth(node.operand)
    if isinstance(node, Binary):
        return 1 + max(depth(node.left), depth(node.right))
    if isinstance(node, Call):
        return 1 + max((depth(arg) for arg in node.args), default=0)
    return 1


def tree_lines(node: Node, indent: int = 0) -> list[str]:
    pad = "  " * indent
    if isinstance(node, Number):
        return [f"{pad}{format_number(node.value)}   {node.level}"]
    if isinstance(node, Name):
        return [f"{pad}{node.identifier}   {node.level}"]
    if isinstance(node, Unary):
        head = f"{pad}{node.op}   {node.level}, column {node.start + 1}"
        return [head, *tree_lines(node.operand, indent + 1)]
    if isinstance(node, Binary):
        head = f"{pad}{node.op}   {node.level}, column {node.start + 1}"
        return [
            head,
            *tree_lines(node.left, indent + 1),
            *tree_lines(node.right, indent + 1),
        ]
    head = f"{pad}{node.name}()   {node.level}, column {node.start + 1}"
    lines = [head]
    for arg in node.args:
        lines.extend(tree_lines(arg, indent + 1))
    return lines

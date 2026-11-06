"""Patterns parsed into a tree, because a tree is what a machine can walk.

The syntax is deliberately small: literals, `.`, character classes, groups,
alternation and the three unbounded repetitions. Everything the engine reports
later is a statement about this tree, so the tree keeps its own printed form and
parsing that form gives the same tree back.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

ALT = 1
CONCAT = 2
REPEAT = 3
ATOM = 4

ANY = "any"
CHAR = "char"
CLASS = "class"
EMPTY = "empty"
CONCAT_KIND = "concat"
ALT_KIND = "alt"


class PatternError(ValueError):
    """A pattern that cannot be read, with the position that stopped it."""

    def __init__(self, message: str, position: int) -> None:
        super().__init__(f"{message} at position {position + 1}")
        self.message = message
        self.position = position

    def caret(self, text: str) -> str:
        return f"  {text}\n  {' ' * self.position}^"


def _merge(ranges: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    merged: list[tuple[int, int]] = []
    for low, high in sorted(ranges):
        if merged and low <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], high))
        else:
            merged.append((low, high))
    return tuple(merged)


@dataclass(frozen=True)
class CharClass:
    """A set of characters, kept as sorted ranges so equality is real equality."""

    ranges: tuple[tuple[int, int], ...]
    negated: bool = False

    @classmethod
    def build(cls, ranges: list[tuple[int, int]], *, negated: bool = False) -> CharClass:
        return cls(_merge(ranges), negated)

    def matches(self, char: str) -> bool:
        inside = any(low <= ord(char) <= high for low, high in self.ranges)
        return inside != self.negated

    def characters(self, limit: int = 128) -> tuple[str, ...]:
        """The characters this class can match, when the set is small enough."""
        found: list[str] = []
        for low, high in self.ranges:
            for code in range(low, min(high, low + limit) + 1):
                found.append(chr(code))
                if len(found) >= limit:
                    return tuple(found)
        return tuple(found)

    def render(self) -> str:
        parts = []
        for low, high in self.ranges:
            if low == high:
                parts.append(render_char(chr(low)))
            else:
                parts.append(f"{render_char(chr(low))}-{render_char(chr(high))}")
        body = "".join(parts)
        return f"[{'^' if self.negated else ''}{body}]"


class Node:
    """Every node knows its printed form and its precedence, and nothing else."""

    kind: ClassVar[str] = "node"
    precedence: ClassVar[int] = ATOM

    def render(self) -> str:
        raise NotImplementedError

    def text(self, minimum: int = 0) -> str:
        printed = self.render()
        return f"({printed})" if self.precedence < minimum else printed


@dataclass(frozen=True)
class Empty(Node):
    kind: ClassVar[str] = EMPTY
    precedence: ClassVar[int] = ATOM

    def render(self) -> str:
        return "()"


@dataclass(frozen=True)
class Char(Node):
    char: str
    kind: ClassVar[str] = CHAR
    precedence: ClassVar[int] = ATOM

    def render(self) -> str:
        return render_char(self.char)


@dataclass(frozen=True)
class Any(Node):
    kind: ClassVar[str] = ANY
    precedence: ClassVar[int] = ATOM

    def render(self) -> str:
        return "."


@dataclass(frozen=True)
class Class(Node):
    char_class: CharClass
    kind: ClassVar[str] = CLASS
    precedence: ClassVar[int] = ATOM

    def render(self) -> str:
        return self.char_class.render()


@dataclass(frozen=True)
class Concat(Node):
    parts: tuple[Node, ...]
    kind: ClassVar[str] = CONCAT_KIND
    precedence: ClassVar[int] = CONCAT

    def render(self) -> str:
        return "".join(part.text(REPEAT) for part in self.parts)


@dataclass(frozen=True)
class Alt(Node):
    options: tuple[Node, ...]
    kind: ClassVar[str] = ALT_KIND
    precedence: ClassVar[int] = ALT

    def render(self) -> str:
        return "|".join(option.text(CONCAT) for option in self.options)


@dataclass(frozen=True)
class Repeat(Node):
    body: Node
    minimum: int
    maximum: int | None
    kind: ClassVar[str] = REPEAT
    precedence: ClassVar[int] = REPEAT

    def render(self) -> str:
        inner = self.body.text(REPEAT + 1)
        if (self.minimum, self.maximum) == (0, None):
            return f"{inner}*"
        if (self.minimum, self.maximum) == (1, None):
            return f"{inner}+"
        if (self.minimum, self.maximum) == (0, 1):
            return f"{inner}?"
        raise ValueError("this engine has only *, + and ?")


_ESCAPES = {".", "*", "+", "?", "(", ")", "|", "[", "]", "\\", "^", "$", "-"}


def render_char(char: str) -> str:
    if char in _ESCAPES:
        return "\\" + char
    if char.isspace():
        return {"\n": "\\n", "\t": "\\t"}.get(char, char)
    return char


class _Cursor:
    def __init__(self, text: str) -> None:
        self.text = text
        self.at = 0

    def peek(self) -> str | None:
        return self.text[self.at] if self.at < len(self.text) else None

    def take(self) -> str:
        char = self.text[self.at]
        self.at += 1
        return char

    def fail(self, message: str) -> None:
        raise PatternError(message, self.at)


class _Parser:
    """Recursive descent: alternation, then concatenation, then repetition."""

    def __init__(self, text: str) -> None:
        self.cursor = _Cursor(text)

    def parse(self) -> Node:
        node = self.alternation()
        if self.cursor.peek() is not None:
            self.cursor.fail(f"{self.cursor.peek()!r} has no place here")
        return node

    def alternation(self) -> Node:
        options = [self.concatenation()]
        while self.cursor.peek() == "|":
            self.cursor.take()
            options.append(self.concatenation())
        if len(options) == 1:
            return options[0]
        return Alt(tuple(options))

    def concatenation(self) -> Node:
        parts: list[Node] = []
        while True:
            char = self.cursor.peek()
            if char is None or char in "|)":
                break
            parts.append(self.repetition())
        if not parts:
            return Empty()
        if len(parts) == 1:
            return parts[0]
        return Concat(tuple(parts))

    def repetition(self) -> Node:
        node = self.atom()
        while True:
            char = self.cursor.peek()
            if char == "*":
                self.cursor.take()
                node = Repeat(node, 0, None)
            elif char == "+":
                self.cursor.take()
                node = Repeat(node, 1, None)
            elif char == "?":
                self.cursor.take()
                node = Repeat(node, 0, 1)
            elif char == "{":
                self.cursor.fail("counted repetition is not in this engine; write the copies")
            else:
                return node

    def atom(self) -> Node:
        char = self.cursor.peek()
        if char is None:
            self.cursor.fail("the pattern ends where an expression was expected")
        if char == "(":
            self.cursor.take()
            node = self.alternation()
            if self.cursor.peek() != ")":
                self.cursor.fail("a group is open and never closed")
            self.cursor.take()
            return node
        if char == "[":
            return self.char_class()
        if char == ".":
            self.cursor.take()
            return Any()
        if char == "\\":
            return self.escape()
        if char in "*+?)|":
            self.cursor.fail(f"{char!r} needs something to repeat or close")
        self.cursor.take()
        return Char(char)

    def escape(self) -> Node:
        self.cursor.take()
        char = self.cursor.peek()
        if char is None:
            self.cursor.fail("a backslash at the end escapes nothing")
        if char == "s":
            self.cursor.take()
            return Class(CharClass.build([(9, 10), (32, 32)]))
        if char == "d":
            self.cursor.take()
            return Class(CharClass.build([(48, 57)]))
        if char == "w":
            self.cursor.take()
            return Class(CharClass.build([(48, 57), (65, 90), (95, 95), (97, 122)]))
        if char == "n":
            self.cursor.take()
            return Char("\n")
        if char == "t":
            self.cursor.take()
            return Char("\t")
        if char in _ESCAPES:
            self.cursor.take()
            return Char(char)
        self.cursor.fail(f"\\{char} is not an escape this engine knows")

    def char_class(self) -> Node:
        self.cursor.take()
        negated = False
        if self.cursor.peek() == "^":
            self.cursor.take()
            negated = True
        ranges: list[tuple[int, int]] = []
        first = True
        while True:
            char = self.cursor.peek()
            if char is None:
                self.cursor.fail("a character class is open and never closed")
            if char == "]" and not first:
                self.cursor.take()
                break
            low = self._class_char()
            if self.cursor.peek() == "-" and self.cursor.text[self.cursor.at :][1:2] not in (
                "]",
                "",
            ):
                self.cursor.take()
                high = self._class_char()
                if ord(high) < ord(low):
                    self.cursor.fail(f"the range {low}-{high} runs backwards")
                ranges.append((ord(low), ord(high)))
            else:
                ranges.append((ord(low), ord(low)))
            first = False
        if not ranges:
            self.cursor.fail("an empty character class matches nothing at all")
        return Class(CharClass.build(ranges, negated=negated))

    def _class_char(self) -> str:
        char = self.cursor.peek()
        if char is None:
            self.cursor.fail("a character class is open and never closed")
        if char == "\\":
            self.cursor.take()
            escaped = self.cursor.peek()
            if escaped is None:
                self.cursor.fail("a backslash at the end escapes nothing")
            self.cursor.take()
            return {"n": "\n", "t": "\t"}.get(escaped, escaped)
        self.cursor.take()
        return char


def parse(text: str) -> Node:
    """Read a pattern, or say exactly where it stopped making sense."""
    if not text:
        raise PatternError("an empty pattern is not a pattern; use () for nothing", 0)
    return _Parser(text).parse()


def alphabet(node: Node) -> str:
    """The characters a pattern mentions, in a stable order, without repeats."""
    seen: set[str] = set()

    def walk(item: Node) -> None:
        if isinstance(item, Char):
            seen.add(item.char)
        elif isinstance(item, Class):
            for char in item.char_class.characters():
                seen.add(char)
        elif isinstance(item, Concat):
            for part in item.parts:
                walk(part)
        elif isinstance(item, Alt):
            for option in item.options:
                walk(option)
        elif isinstance(item, Repeat):
            walk(item.body)

    walk(node)
    return "".join(sorted(seen))


def unmentioned_char(node: Node) -> str:
    """A character the pattern cannot tell apart from any other it ignores."""
    used = set(alphabet(node))
    for code in range(ord("A"), ord("A") + 200):
        char = chr(code)
        if char not in used:
            return char
    raise PatternError("no unmentioned character is left in this alphabet", 0)

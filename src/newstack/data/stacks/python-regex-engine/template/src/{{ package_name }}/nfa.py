"""A Thompson construction and a simulation that never backtracks.

Each fragment has exactly one way in and one way out, which is what makes the
nesting compose: no fragment ever needs to know what surrounds it. The accept
state has no outgoing edge, so finishing early cannot be undone. Simulating the
machine means carrying a set of states and stepping every state in the set at
once — one pass per character, whatever the pattern looks like inside.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import syntax

CHAR = "char"
ANY = "any"
CLASS = "class"


@dataclass(frozen=True)
class Label:
    """What an edge accepts: one character, anything, or a class."""

    kind: str
    char: str = ""
    char_class: syntax.CharClass | None = None

    def matches(self, char: str) -> bool:
        if self.kind == ANY:
            return True
        if self.kind == CHAR:
            return char == self.char
        assert self.char_class is not None
        return self.char_class.matches(char)

    def text(self) -> str:
        if self.kind == ANY:
            return "."
        if self.kind == CHAR:
            return syntax.render_char(self.char)
        assert self.char_class is not None
        return self.char_class.render()


class _Builder:
    def __init__(self) -> None:
        self.edges: list[tuple[int, Label | None, int]] = []
        self.count = 0

    def state(self) -> int:
        number = self.count
        self.count += 1
        return number

    def edge(self, source: int, label: Label | None, target: int) -> None:
        self.edges.append((source, label, target))


def _compile(node: syntax.Node, builder: _Builder) -> tuple[int, int]:
    if isinstance(node, syntax.Empty):
        start, end = builder.state(), builder.state()
        builder.edge(start, None, end)
        return start, end
    if isinstance(node, syntax.Char):
        start, end = builder.state(), builder.state()
        builder.edge(start, Label(CHAR, char=node.char), end)
        return start, end
    if isinstance(node, syntax.Any):
        start, end = builder.state(), builder.state()
        builder.edge(start, Label(ANY), end)
        return start, end
    if isinstance(node, syntax.Class):
        start, end = builder.state(), builder.state()
        builder.edge(start, Label(CLASS, char_class=node.char_class), end)
        return start, end
    if isinstance(node, syntax.Concat):
        current: tuple[int, int] | None = None
        for part in node.parts:
            start, end = _compile(part, builder)
            if current is None:
                current = (start, end)
            else:
                builder.edge(current[1], None, start)
                current = (current[0], end)
        assert current is not None
        return current
    if isinstance(node, syntax.Alt):
        start, end = builder.state(), builder.state()
        for option in node.options:
            inner_start, inner_end = _compile(option, builder)
            builder.edge(start, None, inner_start)
            builder.edge(inner_end, None, end)
        return start, end
    if isinstance(node, syntax.Repeat):
        start, end = builder.state(), builder.state()
        inner_start, inner_end = _compile(node.body, builder)
        builder.edge(start, None, inner_start)
        builder.edge(inner_end, None, end)
        if node.minimum == 0:
            builder.edge(start, None, end)
        if node.maximum is None:
            builder.edge(inner_end, None, inner_start)
        return start, end
    raise TypeError(f"no fragment is defined for {node!r}")


@dataclass(frozen=True)
class Nfa:
    """The compiled machine: states, labelled edges, one start and one accept."""

    pattern: str
    start: int
    accept: int
    states: int
    edges: tuple[tuple[int, Label | None, int], ...]

    def outgoing(self) -> dict[int, list[tuple[Label | None, int]]]:
        table: dict[int, list[tuple[Label | None, int]]] = {}
        for source, label, target in self.edges:
            table.setdefault(source, []).append((label, target))
        return table

    def epsilon_closure(self, states: frozenset[int]) -> frozenset[int]:
        table = self.outgoing()
        seen = set(states)
        stack = list(states)
        while stack:
            state = stack.pop()
            for label, target in table.get(state, ()):
                if label is None and target not in seen:
                    seen.add(target)
                    stack.append(target)
        return frozenset(seen)

    def step(self, states: frozenset[int], char: str) -> frozenset[int]:
        table = self.outgoing()
        reached: set[int] = set()
        for state in states:
            for label, target in table.get(state, ()):
                if label is not None and label.matches(char):
                    reached.add(target)
        return self.epsilon_closure(frozenset(reached))

    def start_states(self) -> frozenset[int]:
        return self.epsilon_closure(frozenset({self.start}))

    def run(self, text: str) -> list[frozenset[int]]:
        """The state set before each character, and the one after the last."""
        sets = [self.start_states()]
        for char in text:
            sets.append(self.step(sets[-1], char))
        return sets

    def accepts(self, states: frozenset[int]) -> bool:
        return self.accept in states

    def matches(self, text: str) -> bool:
        return self.accepts(self.run(text)[-1])

    def accepts_prefix(self, text: str) -> int | None:
        """The length of the longest prefix that is accepted, or None."""
        sets = self.run(text)
        longest = None
        for index, states in enumerate(sets):
            if self.accepts(states):
                longest = index
        return longest

    def dead_end(self, states: frozenset[int]) -> bool:
        return not states

    def edge_count(self) -> int:
        return len(self.edges)

    def epsilon_count(self) -> int:
        return sum(1 for _, label, _ in self.edges if label is None)

    def accept_is_final(self) -> bool:
        return all(source != self.accept for source, _, _ in self.edges)

    def lines(self) -> list[str]:
        return [
            f"nfa        {self.states} state(s), {self.edge_count()} edge(s), "
            f"{self.epsilon_count()} of them silent",
            f"accept     state {self.accept}, with no way out: {self.accept_is_final()}",
        ]


def compile_text(text: str) -> tuple[syntax.Node, Nfa]:
    """Parse and compile in one step, since no caller wants only half."""
    node = syntax.parse(text)
    builder = _Builder()
    start, accept = _compile(node, builder)
    return node, Nfa(
        pattern=text,
        start=start,
        accept=accept,
        states=builder.count,
        edges=tuple(builder.edges),
    )


def compile_node(node: syntax.Node, text: str = "") -> Nfa:
    builder = _Builder()
    start, accept = _compile(node, builder)
    return Nfa(
        pattern=text or node.render(),
        start=start,
        accept=accept,
        states=builder.count,
        edges=tuple(builder.edges),
    )

"""The other engine, kept only to count what it costs.

This is a textbook backtracking matcher: it walks the tree, tries an alternative,
and when the rest of the pattern fails it comes back and tries the next one. It
answers correctly, and on a pattern like `(a*)*b` it takes exponentially many
steps to say no, because nothing remembers that it has already been in this
position with this input. It exists so the simulation can be compared against a
number instead of an adjective.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from . import syntax

DEFAULT_CAP = 2_000_000


class BacktrackError(RuntimeError):
    """The backtracking matcher ran past the budget it was given."""


@dataclass(frozen=True)
class Steps:
    """What the naive engine cost, and what it concluded."""

    pattern: str
    text: str
    steps: int
    matched: bool
    capped: bool

    def line(self) -> str:
        verdict = "matched" if self.matched else "did not match"
        return f"backtrack  {self.steps} step(s) to say it {verdict}"


class _Budget:
    def __init__(self, cap: int) -> None:
        self.cap = cap
        self.steps = 0

    def spend(self) -> None:
        self.steps += 1
        if self.steps > self.cap:
            raise BacktrackError(
                f"the backtracking matcher spent {self.cap} step(s) and had not "
                "finished; that is the growth, not a bug in the count"
            )


def _ends(node: syntax.Node, text: str, at: int, budget: _Budget) -> Iterator[int]:
    budget.spend()
    if isinstance(node, syntax.Empty):
        yield at
        return
    if isinstance(node, syntax.Char):
        if at < len(text) and text[at] == node.char:
            yield at + 1
        return
    if isinstance(node, syntax.Any):
        if at < len(text):
            yield at + 1
        return
    if isinstance(node, syntax.Class):
        if at < len(text) and node.char_class.matches(text[at]):
            yield at + 1
        return
    if isinstance(node, syntax.Concat):
        parts = node.parts

        def run(index: int, position: int) -> Iterator[int]:
            if index == len(parts):
                yield position
                return
            for end in _ends(parts[index], text, position, budget):
                yield from run(index + 1, end)

        yield from run(0, at)
        return
    if isinstance(node, syntax.Alt):
        for option in node.options:
            yield from _ends(option, text, at, budget)
        return
    if isinstance(node, syntax.Repeat):
        minimum = node.minimum
        maximum = node.maximum

        def repeat(count: int, position: int) -> Iterator[int]:
            budget.spend()
            if count < minimum:
                for end in _ends(node.body, text, position, budget):
                    if end == position:
                        continue
                    yield from repeat(count + 1, end)
                return
            if maximum is None or count < maximum:
                for end in _ends(node.body, text, position, budget):
                    if end == position:
                        continue
                    yield from repeat(count + 1, end)
            yield position

        yield from repeat(0, at)
        return
    raise TypeError(f"no matcher is defined for {node!r}")


def count(node: syntax.Node, text: str, *, cap: int = DEFAULT_CAP) -> Steps:
    """Run the naive engine to completion against a step budget."""
    budget = _Budget(cap)
    matched = False
    try:
        for end in _ends(node, text, 0, budget):
            if end == len(text):
                matched = True
                break
    except BacktrackError:
        return Steps(node.render(), text, budget.steps, False, True)
    return Steps(node.render(), text, budget.steps, matched, False)


def count_pattern(pattern: str, text: str, *, cap: int = DEFAULT_CAP) -> Steps:
    return count(syntax.parse(pattern), text, cap=cap)

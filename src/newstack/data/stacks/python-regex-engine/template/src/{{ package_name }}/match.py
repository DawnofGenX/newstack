"""Whole-string matching and leftmost search, both on top of one simulation.

`search` is not a second engine: it asks the same machine about each start offset
and keeps the longest answer at the first offset that answers at all. Leftmost
first, then longest, is the rule an operator can check by hand.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import nfa as nfa_module
from . import syntax


@dataclass(frozen=True)
class Match:
    """A span of the text, as offsets into the text that was searched."""

    text: str
    start: int
    end: int

    @property
    def value(self) -> str:
        return self.text[self.start : self.end]

    @property
    def length(self) -> int:
        return self.end - self.start

    def line(self) -> str:
        return f"match      [{self.start}, {self.end}) {self.value!r}"


def full_matches(node: syntax.Node, text: str) -> bool:
    return nfa_module.compile_node(node, node.render()).matches(text)


def full(node: syntax.Node, text: str) -> str | None:
    """The whole text, or None: a match that has to end where the text ends."""
    machine = nfa_module.compile_node(node, node.render())
    return text if machine.matches(text) else None


def search(node: syntax.Node, text: str) -> Match | None:
    """Leftmost, then longest: the first start offset that can match at all."""
    machine = nfa_module.compile_node(node, node.render())
    for start in range(len(text) + 1):
        longest = machine.accepts_prefix(text[start:])
        if longest is not None:
            return Match(text, start, start + longest)
    return None


def all_matches(node: syntax.Node, text: str, *, limit: int = 1000) -> list[Match]:
    """Every non-overlapping leftmost match, moving past each one it reports."""
    machine = nfa_module.compile_node(node, node.render())
    found: list[Match] = []
    at = 0
    while at <= len(text) and len(found) < limit:
        for start in range(at, len(text) + 1):
            longest = machine.accepts_prefix(text[start:])
            if longest is not None:
                found.append(Match(text, start, start + longest))
                at = start + max(longest, 1)
                break
        else:
            break
    return found


def describe(node: syntax.Node, text: str) -> list[str]:
    machine = nfa_module.compile_node(node, node.render())
    found = search(node, text)
    lines = [
        f"pattern    {node.render()}",
        f"text       {text!r}",
        f"whole      {'matches the text exactly' if machine.matches(text) else 'no'}",
    ]
    if found is None:
        lines.append("search     no non-empty run of this text matches anywhere")
    else:
        lines.append(found.line())
    return lines

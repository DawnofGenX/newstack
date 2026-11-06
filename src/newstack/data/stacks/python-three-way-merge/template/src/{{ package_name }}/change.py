"""Turn a base text and an edited text into the changes between them."""

from __future__ import annotations

import difflib
from dataclasses import dataclass


@dataclass(frozen=True)
class Change:
    """A single edit: replace base[start:end] with ``lines``.

    An insertion has ``start == end`` and empty ``replaces``; a deletion has
    empty ``lines``. Both are ordinary changes, which is what lets the merge
    treat them with one rule instead of four.
    """

    start: int
    end: int
    lines: tuple[str, ...]

    @property
    def inserted(self) -> bool:
        return self.start == self.end

    @property
    def deleted(self) -> bool:
        return not self.lines

    @property
    def replaced(self) -> int:
        return self.end - self.start

    def touches(self, other: Change) -> bool:
        """True when two changes cannot both be applied without an ordering.

        Two edits conflict when their base ranges intersect, and when both are
        insertions at the very same point: there is no order in the base to
        say which one comes first, so the merge must not invent one.
        """
        if self.inserted and other.inserted:
            return self.start == other.start
        return self.start < other.end and other.start < self.end

    def line(self, number: int) -> str:
        if self.inserted:
            what = f"insert {len(self.lines)} line(s) at {self.start}"
        elif self.deleted:
            what = f"delete base {self.start}..{self.end}"
        else:
            what = f"replace base {self.start}..{self.end} with {len(self.lines)} line(s)"
        return f"{number:>2}  {what}"


def split_lines(text: str) -> list[str]:
    """Lines that keep their endings, so a missing final newline survives."""
    return text.splitlines(keepends=True)


def changes(base: str | list[str], other: str | list[str]) -> list[Change]:
    """The edits that turn ``base`` into ``other``, in base order.

    ``autojunk`` is off on purpose: its heuristic calls repeated lines junk and
    then reports an edit where nothing changed. A merge that invents edits is
    worse than one that is slow.
    """
    base_lines = split_lines(base) if isinstance(base, str) else list(base)
    other_lines = split_lines(other) if isinstance(other, str) else list(other)
    matcher = difflib.SequenceMatcher(None, base_lines, other_lines, autojunk=False)
    found: list[Change] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        found.append(Change(i1, i2, tuple(other_lines[j1:j2])))
    return found

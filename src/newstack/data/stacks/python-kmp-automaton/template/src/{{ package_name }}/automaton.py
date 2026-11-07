"""Knuth-Morris-Pratt: the failure table and the scan that trusts it.

In this automaton the failure link never forgets a border it owes:
the link at state ``k`` is the longest proper border of the first
``k`` pattern letters — the naive border count, computed once.
The scan rides the text letter by letter and, on a miss, falls back
along those links instead of rewinding. Overlaps are counted, not
skipped: after a hit the scan keeps the tail the border allows, so
``ana`` inside ``banana`` starts twice. Every start the scan reports
must equal the naive scan's, and every link must equal the border
count, checked, never assumed.
"""

from __future__ import annotations

from .naive import border_length
from .pattern import PatternError, ensure_pattern, ensure_text


class AutomatonError(ValueError):
    """The automaton was handed something it cannot answer."""


def failure_table(pattern: str) -> tuple[int, ...]:
    """The failure link per state: table[k] is the border of pattern[:k].

    State ``k`` means ``k`` pattern letters are matched; a miss
    retreats to ``table[k]``, never below. The empty pattern owns the
    single link ``(0,)``.
    """
    try:
        word = ensure_pattern(pattern)
    except PatternError as refusal:
        raise AutomatonError(f"no table for that: {refusal}") from refusal
    links = [0] * (len(word) + 1)
    for state in range(2, len(word) + 1):
        step = links[state - 1]
        while step > 0 and word[state - 1] != word[step]:
            step = links[step]
        if word[state - 1] == word[step]:
            step += 1
        links[state] = step
    return tuple(links)


def scan_starts(text: str, pattern: str) -> list[int]:
    """Every start where the pattern sits in the text, overlaps kept."""
    try:
        hay = ensure_text(text)
        needle = ensure_pattern(pattern)
    except PatternError as refusal:
        raise AutomatonError(f"no scan for that: {refusal}") from refusal
    if not needle:
        return list(range(len(hay) + 1))
    links = failure_table(needle)
    starts: list[int] = []
    state = 0
    for offset, letter in enumerate(hay):
        while state > 0 and letter != needle[state]:
            state = links[state]
        if letter == needle[state]:
            state += 1
        if state == len(needle):
            starts.append(offset - state + 1)
            state = links[state]
    return starts


class KmpAutomaton:
    """A pattern, its failure table, and the questions it answers."""

    def __init__(self, pattern: str) -> None:
        self._pattern = ensure_pattern(pattern)
        self._table = failure_table(self._pattern)

    @property
    def pattern(self) -> str:
        return self._pattern

    @property
    def table(self) -> tuple[int, ...]:
        return self._table

    def find_all(self, text: str) -> list[int]:
        """Every start in order, overlaps counted as real starts."""
        return scan_starts(text, self._pattern)

    def find_first(self, text: str) -> int | None:
        """The leftmost start, or None when the pattern never sits."""
        starts = self.find_all(text)
        return starts[0] if starts else None

    def count(self, text: str) -> int:
        """How many starts the text owes, empty pattern included."""
        return len(self.find_all(text))

    def audit(self) -> list[str]:
        """Every link against the naive border count; silent when clean."""
        faults: list[str] = []
        for state, link in enumerate(self._table):
            honest = border_length(self._pattern[:state])
            if link != honest:
                faults.append(f"state {state}: link {link} != border {honest}")
        return faults

    def __len__(self) -> int:
        return len(self._pattern)

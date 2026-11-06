"""The naive scanner: the reference the automaton must never disagree with.

One pattern at a time, one window per start position. It is deliberately
slow — its job is to be obviously right so the sweep can be proven against
it. It also counts what it looks at, because the counter story is exactly
this: same hits, fewer inspections.
"""

from __future__ import annotations

from dataclasses import dataclass

from .automaton import Hit

__all__ = ["NaiveReport", "naive_sweep"]


@dataclass(frozen=True)
class NaiveReport:
    """The naive answer: the hits (sorted like a sweep's) and the inspections."""

    hits: tuple[Hit, ...]
    inspections: int

    def __len__(self) -> int:
        return len(self.hits)


def naive_sweep(text: str, patterns: list[str] | tuple[str, ...]) -> NaiveReport:
    """Scan each pattern separately over every start: O(text * patterns).

    Ties land in the same deterministic order a sweep publishes: by end,
    then start, then the pattern itself.
    """
    found: list[Hit] = []
    inspections = 0
    for pattern in patterns:
        if not pattern:
            continue
        width = len(pattern)
        for start in range(0, len(text) - width + 1):
            inspections += 1
            if text[start : start + width] == pattern:
                found.append(Hit(start + width - 1, start, pattern))
    found.sort(key=lambda hit: (hit.end, hit.start, hit.pattern))
    return NaiveReport(tuple(found), inspections)

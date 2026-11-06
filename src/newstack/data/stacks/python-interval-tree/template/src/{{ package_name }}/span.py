"""Half-open integer spans: the shape a stab and an overlap both ask about.

An interval names every integer from `start` up to but NOT including `end`.
Touching is not overlapping: [1..3) and [3..5) share the point 3 only as the
right end of the first, which the first does not name, so the two never
collide and a stab at 3 lands in the second alone.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Interval", "SpanError"]


class SpanError(ValueError):
    """A span was named that no half-open interval can answer for."""


@dataclass(frozen=True, order=True)
class Interval:
    """The half-open span [start, end) over integers; end is never inside."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if not isinstance(self.start, int) or isinstance(self.start, bool):
            raise SpanError(f"{self.start!r} is not an integer start")
        if not isinstance(self.end, int) or isinstance(self.end, bool):
            raise SpanError(f"{self.end!r} is not an integer end")
        if self.start >= self.end:
            raise SpanError(f"[{self.start}..{self.end}) is empty: ends never count")

    def holds(self, point: int) -> bool:
        """Whether `point` stands inside: start counts, the right end does not."""
        return self.start <= point < self.end

    def overlaps(self, other: Interval) -> bool:
        """Whether the two share at least one integer point."""
        return self.start < other.end and other.start < self.end

    def display(self) -> str:
        return f"[{self.start}..{self.end})"

"""The oracle: a linear scan nobody needs to trust.

The tree exists to answer faster; the scan exists to say whether faster was
correct. Every stabbing and overlap answer the tree gives is checked here
first, so "equal to the brute-force scan" is a computed comparison and never
an assertion in a comment.
"""

from __future__ import annotations

from .span import Interval

__all__ = ["scan_overlap", "scan_stab"]


def scan_stab(spans: list[Interval], point: int) -> list[Interval]:
    """Every span holding the point, in (start, end) order, one test each."""
    return sorted(span for span in spans if span.holds(point))


def scan_overlap(spans: list[Interval], low: int, high: int) -> list[Interval]:
    """Every span touching [low, high), in (start, end) order, one test each."""
    window = Interval(low, high)
    return sorted(span for span in spans if span.overlaps(window))

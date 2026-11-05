"""Reading builders, so the tests read as timelines instead of arithmetic."""

from __future__ import annotations

from collections.abc import Sequence

from {{ package_name }} import model

MICROSECONDS = model.MICROSECONDS


def readings(pairs: Sequence[tuple[int, int]]) -> list[model.Sample]:
    """`[(0, 0), (10, 100)]` means 10 s into the run the counter read 100."""
    return [model.Sample(at_us=at * MICROSECONDS, value=value) for at, value in pairs]

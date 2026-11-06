"""Reading a stream of identifiers back: order, duplicates, and rate."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

from .layout import EPOCH_MS, LayoutError, compose, decode


@dataclass(frozen=True)
class Report:
    """What a stream of identifiers says about the generator that made it."""

    count: int
    distinct: int
    duplicates: int
    monotone: bool
    out_of_order: int
    workers: tuple[int, ...]
    span_ms: int
    per_second: float

    def lines(self) -> list[str]:
        workers = ", ".join(str(worker) for worker in self.workers) or "(none)"
        order = "strictly increasing" if self.monotone else f"{self.out_of_order} step(s) back"
        return [
            f"identifiers  {self.count}",
            f"distinct     {self.distinct} ({self.duplicates} duplicate(s))",
            f"order        {order}",
            f"workers      {workers}",
            f"span         {self.span_ms} ms",
            f"rate         {self.per_second:,.0f} identifier(s) per second",
        ]

    def held(self) -> bool:
        return self.duplicates == 0 and self.monotone


def audit(values: list[int], *, epoch_ms: int = EPOCH_MS) -> Report:
    if not values:
        raise LayoutError("an empty stream says nothing about the generator")
    decoded = [decode(value) for value in values]
    back = sum(1 for left, right in pairwise(values) if right <= left)
    span = decoded[-1].relative_ms - decoded[0].relative_ms
    seconds = span / 1_000 if span else 0.0
    return Report(
        count=len(values),
        distinct=len(set(values)),
        duplicates=len(values) - len(set(values)),
        monotone=back == 0,
        out_of_order=back,
        workers=tuple(sorted({item.worker for item in decoded})),
        span_ms=span,
        per_second=(len(values) / seconds) if seconds else 0.0,
    )


def collision(worker_a: int, worker_b: int, *, relative_ms: int) -> tuple[int, int]:
    """Two workers, one millisecond, one sequence: the identifiers must differ."""
    left = compose(relative_ms, worker_a, 0)
    right = compose(relative_ms, worker_b, 0)
    return left, right


def spacing(values: list[int]) -> int:
    """The smallest gap between consecutive identifiers, in sequence steps."""
    if len(values) < 2:
        raise LayoutError("spacing needs at least two identifiers")
    return min(right - left for left, right in pairwise(values))


def epoch_note(epoch_ms: int = EPOCH_MS) -> str:
    return f"identifiers are relative to {epoch_ms} ms, so the epoch is part of the meaning"

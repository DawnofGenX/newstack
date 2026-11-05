"""The comparison that makes an estimate trustworthy: error beside the promise."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .hll import HyperLogLog, relative_error


@dataclass(frozen=True)
class Comparison:
    """One estimate, the truth, and how far apart they are."""

    n: int
    estimate: int
    bound: float
    sigma: float

    @property
    def error(self) -> float:
        if self.n == 0:
            return 0.0
        return (self.estimate - self.n) / self.n

    @property
    def within(self) -> bool:
        """The standard error is a 1-sigma promise; four of them is the bar here."""
        return abs(self.error) <= 4.0 * self.bound

    def line(self) -> str:
        return (
            f"{self.n:>9}  {self.estimate:>9}  {self.error * 100:+7.2f}%  "
            f"{self.bound * 100:5.2f}%  {'yes' if self.within else 'NO'}"
        )


def compare(sketch: HyperLogLog, n: int) -> Comparison:
    return Comparison(
        n=n,
        estimate=sketch.count(),
        bound=relative_error(sketch.precision),
        sigma=0,
    )


def error_at(precision: int, values: list[int], n: int) -> Comparison:
    """Feed pre-hashed values so a table can be built from one hash pass."""
    sketch = HyperLogLog(precision)
    for value in values:
        sketch.add_hash(value)
    return compare(sketch, n)


def table_head() -> str:
    return "  distinct  estimate     error  promised  within"


def table(precisions_and_values, ) -> list[Comparison]:
    return [error_at(precision, values, n) for precision, values, n in precisions_and_values]


def least_precision_for(error: float) -> int:
    """The smallest precision whose promised error is at most the one asked for."""
    for precision in range(4, 19):
        if relative_error(precision) <= error:
            return precision
    raise ValueError(f"no precision promises an error as small as {error}")


def set_memory(items: set[str]) -> int:
    """Roughly what an exact set costs: the set itself plus its strings."""
    return items.__sizeof__() + sum(item.__sizeof__() for item in items)


def kib(bytes_used: int) -> str:
    return f"{bytes_used / 1024:.1f} KiB"


def log2_safe(value: float) -> float:
    return math.log2(value)

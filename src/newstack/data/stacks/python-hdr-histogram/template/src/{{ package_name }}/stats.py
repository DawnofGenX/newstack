"""The truth, so the histogram can be checked instead of trusted."""

from __future__ import annotations

import math
from dataclasses import dataclass


class StatsError(ValueError):
    """A comparison that has no answer without the raw samples."""


def nearest_rank(values: list[int], percentile: float) -> int:
    """The exact percentile of the raw samples, by the same rule the histogram uses.

    Nearest rank, one-based: the answer is the value at position
    ``ceil(p / 100 * n)`` in the sorted samples. Any other rule (linear
    interpolation, the mean of two neighbours) would make the comparison between a
    histogram and the truth a comparison of two definitions.
    """
    if not values:
        raise StatsError("a percentile of no samples is not a number")
    if not 0 < percentile <= 100:
        raise StatsError(f"a percentile is above 0 and at most 100, not {percentile}")
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile / 100.0 * len(ordered)))
    return ordered[rank - 1]


def mean(values: list[int]) -> float:
    if not values:
        raise StatsError("the mean of no samples is not a number")
    return sum(values) / len(values)


@dataclass(frozen=True)
class Row:
    """One percentile: what the histogram says, what the samples say, and the gap."""

    percentile: float
    reported: int
    truth: int
    relative_error: float

    def line(self) -> str:
        return (
            f"  p{self.percentile:<5g} reported {self.reported:>10} "
            f"truth {self.truth:>10} gap {self.relative_error * 100:>8.4f}%"
        )


@dataclass(frozen=True)
class Check:
    """The whole comparison, including the claim it is checking."""

    samples: int
    promised: float
    rows: tuple[Row, ...]

    @property
    def worst(self) -> float:
        return max((row.relative_error for row in self.rows), default=0.0)

    def held(self) -> bool:
        """The promise: every reported value is within the promised error of the truth.

        The histogram reports the ceiling of a bucket, so its answer is never below the
        truth; a report that is *far* above it means the buckets are wider than the
        promise, which is the bug this check exists to catch.
        """
        return self.worst <= self.promised

    def lines(self) -> list[str]:
        lines = [row.line() for row in self.rows]
        lines.append(
            f"  worst gap {self.worst * 100:.4f}% against a promised "
            f"{self.promised * 100:.4f}%: {'held' if self.held() else 'BROKEN'}"
        )
        return lines


def check(
    histogram, values: list[int], points: tuple[float, ...] = (50.0, 90.0, 99.0, 99.9)
) -> Check:
    """Recorded histogram against the raw samples it was built from."""
    if histogram.count() != len(values):
        raise StatsError(
            f"the histogram holds {histogram.count()} sample(s) but {len(values)} were given"
        )
    rows = []
    for point in points:
        reported = histogram.percentile(point)
        truth = nearest_rank(values, point)
        gap = abs(reported - truth) / truth if truth else 0.0
        rows.append(Row(point, reported, truth, gap))
    return Check(len(values), histogram.error, tuple(rows))


def average_of_percentiles(groups: list[dict[str, float]], point: str) -> float:
    """The number a dashboard shows when it averages percentiles: not a percentile."""
    if not groups:
        raise StatsError("averaging no percentiles is not a number")
    return sum(group[point] for group in groups) / len(groups)


def pooled_percentile(groups: list[list[int]], percentile: float) -> int:
    """The percentile of everything together, which is what the average pretends to be."""
    pooled: list[int] = []
    for group in groups:
        pooled.extend(group)
    return nearest_rank(pooled, percentile)


def bytes_per_sample(histogram, samples: int) -> float:
    """The cost of this histogram per recorded sample, in bytes."""
    if samples < 1:
        raise StatsError(f"a per-sample cost needs at least one sample, not {samples}")
    return histogram.bytes_used / samples

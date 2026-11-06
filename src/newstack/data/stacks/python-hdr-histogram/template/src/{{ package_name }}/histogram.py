"""Bucketed latencies: a percentile from a bucket can only be as precise as the bucket.

The layout is the one HdrHistogram uses, from first principles:

* values below ``2 ** significant_bits`` are recorded exactly, one counter each;
* above that, each power of two is cut into ``2 ** significant_bits`` buckets, so a
  recorded value is only ever stored as the bucket that contains it;
* the bucket is at most ``1 / 2 ** significant_bits`` wide relative to its floor, which is
  the error this module promises, prints, and measures.

That is the trade: counts stay exact, values do not, and the error is bounded rather
than hoped for. A reservoir or a sampled percentile has no such bound.
"""

from __future__ import annotations

import math

DEFAULT_SIGNIFICANT_BITS = 10
MIN_SIGNIFICANT_BITS = 1
MAX_SIGNIFICANT_BITS = 16
DEFAULT_MAX_VALUE = 1 << 40


class HistogramError(ValueError):
    """A histogram, an index, or a percentile that cannot be answered as asked."""


def sub_buckets(significant_bits: int) -> int:
    """How many buckets one power of two is cut into."""
    if isinstance(significant_bits, bool) or not isinstance(significant_bits, int):
        raise HistogramError(f"significant bits are a whole number, not {significant_bits!r}")
    if not MIN_SIGNIFICANT_BITS <= significant_bits <= MAX_SIGNIFICANT_BITS:
        raise HistogramError(
            f"significant bits must be between {MIN_SIGNIFICANT_BITS} and "
            f"{MAX_SIGNIFICANT_BITS}, not {significant_bits}"
        )
    return 1 << significant_bits


def relative_error(significant_bits: int) -> float:
    """The promised error: a recorded value is never off by more than this fraction."""
    return 1.0 / sub_buckets(significant_bits)


def index_of(value: int, significant_bits: int = DEFAULT_SIGNIFICANT_BITS) -> int:
    """The counter a value belongs to. Monotone, so counting order is value order."""
    size = sub_buckets(significant_bits)
    if isinstance(value, bool) or not isinstance(value, int):
        raise HistogramError(f"a latency is a whole number of units, not {value!r}")
    if value < 0:
        raise HistogramError(f"a latency cannot be negative, and {value} is")
    if value < size:
        return value
    shift = value.bit_length() - 1 - significant_bits
    bucket = value.bit_length() - significant_bits
    sub = value >> shift
    return bucket * size + (sub - size)


def floor_of(index: int, significant_bits: int = DEFAULT_SIGNIFICANT_BITS) -> int:
    """The lowest value that lands in this counter."""
    size = sub_buckets(significant_bits)
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        raise HistogramError(f"an index is a whole number of at least zero, not {index!r}")
    if index < size:
        return index
    bucket, offset = divmod(index, size)
    return (offset + size) << (bucket - 1)


def ceiling_of(index: int, significant_bits: int = DEFAULT_SIGNIFICANT_BITS) -> int:
    """The highest value that lands in this counter: the honest thing to report."""
    size = sub_buckets(significant_bits)
    if index < size:
        return index
    bucket, _ = divmod(index, size)
    return floor_of(index, significant_bits) + (1 << (bucket - 1)) - 1


def width_of(index: int, significant_bits: int = DEFAULT_SIGNIFICANT_BITS) -> int:
    """How many values share this counter. One means the value is exact."""
    return ceiling_of(index, significant_bits) - floor_of(index, significant_bits) + 1


class Histogram:
    """Counts per bucket, plus the exact count, sum, minimum and maximum."""

    __slots__ = ("_counts", "_max_value", "lowest", "significant_bits", "total", "total_sum")

    def __init__(
        self,
        significant_bits: int = DEFAULT_SIGNIFICANT_BITS,
        *,
        max_value: int = DEFAULT_MAX_VALUE,
        counts: dict[int, int] | None = None,
        total: int = 0,
        total_sum: int = 0,
        lowest: int | None = None,
    ) -> None:
        self.significant_bits = significant_bits
        sub_buckets(significant_bits)
        self._max_value = max_value
        self._counts: dict[int, int] = {}
        self.total = 0
        self.total_sum = 0
        self.lowest: int | None = None
        if counts:
            for index, count in counts.items():
                if count < 0:
                    raise HistogramError(f"a bucket count cannot be negative, and {count} is")
                if count:
                    self._counts[index] = count
                    self.total += count
        if total and total != self.total:
            raise HistogramError(f"the counts add up to {self.total} but the total says {total}")
        if total_sum:
            self.total_sum = total_sum
        if lowest is not None:
            self.lowest = lowest

    @property
    def error(self) -> float:
        """The promised relative error of any reported value."""
        return relative_error(self.significant_bits)

    @property
    def buckets_used(self) -> int:
        return len(self._counts)

    @property
    def bytes_used(self) -> int:
        """The counters that exist, at eight bytes each, plus a fixed header."""
        if not self._counts:
            return 64
        return 8 * (max(self._counts) + 1) + 64

    def record(self, value: int) -> None:
        index = index_of(value, self.significant_bits)
        if index > self._capacity:
            raise HistogramError(
                f"this histogram holds values up to {self._max_value} at "
                f"{self.significant_bits} significant bits, and {value} is past that"
            )
        self._counts[index] = self._counts.get(index, 0) + 1
        self.total += 1
        self.total_sum += value
        self.lowest = value if self.lowest is None else min(self.lowest, value)

    @property
    def _capacity(self) -> int:
        """The highest index this layout was sized for."""
        return index_of(self._max_value, self.significant_bits)

    def record_many(self, values) -> None:
        for value in values:
            self.record(value)

    def count(self) -> int:
        return self.total

    def mean(self) -> float:
        """Exact: the sum is kept beside the counters, so the mean is not bucketed."""
        if not self.total:
            raise HistogramError("the mean of no samples is not a number")
        return self.total_sum / self.total

    def rank_index(self, rank: int) -> int:
        """The bucket that holds the ``rank``-th smallest sample, one-based."""
        if rank < 1 or rank > self.total:
            raise HistogramError(f"rank {rank} is not in a histogram of {self.total} sample(s)")
        seen = 0
        for index in sorted(self._counts):
            seen += self._counts[index]
            if seen >= rank:
                return index
        raise HistogramError("the counters do not add up to the total, so no rank exists")

    def value_at_rank(self, rank: int) -> int:
        """The highest value in the bucket of that rank: never below the truth."""
        return ceiling_of(self.rank_index(rank), self.significant_bits)

    def percentile(self, percentile: float) -> int:
        """Nearest-rank percentile, reported at the ceiling of its bucket."""
        if not self.total:
            raise HistogramError("a percentile of no samples is not a number")
        if not 0 < percentile <= 100:
            raise HistogramError(f"a percentile is above 0 and at most 100, not {percentile}")
        return self.value_at_rank(max(1, math.ceil(percentile / 100.0 * self.total)))

    def percentiles(self, points) -> dict[float, int]:
        return {float(point): self.percentile(float(point)) for point in points}

    def merged(self, other: Histogram) -> Histogram:
        """Pointwise addition: exact, because counts are counts."""
        self._same_layout(other)
        counts = dict(self._counts)
        for index, count in other._counts.items():
            counts[index] = counts.get(index, 0) + count
        lowest = self.lowest
        if other.lowest is not None:
            lowest = other.lowest if lowest is None else min(lowest, other.lowest)
        return Histogram(
            self.significant_bits,
            max_value=max(self._max_value, other._max_value),
            counts=counts,
            total_sum=self.total_sum + other.total_sum,
            lowest=lowest,
        )

    def _same_layout(self, other: Histogram) -> None:
        if other.significant_bits != self.significant_bits:
            raise HistogramError(
                f"cannot merge {other.significant_bits} significant bits into "
                f"{self.significant_bits}: the bucket boundaries would not line up"
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "type": "hdr-histogram",
            "significant_bits": self.significant_bits,
            "max_value": self._max_value,
            "error": self.error,
            "total": self.total,
            "total_sum": self.total_sum,
            "lowest": self.lowest,
            "counts": {str(index): count for index, count in sorted(self._counts.items())},
        }


def parse_histogram(payload: object) -> Histogram:
    """Read the dictionary form back, with the layout named in the error when it cannot."""
    if not isinstance(payload, dict) or payload.get("type") != "hdr-histogram":
        raise HistogramError("this is not a histogram written by this package")
    bits = payload.get("significant_bits")
    if isinstance(bits, bool) or not isinstance(bits, int):
        raise HistogramError("a histogram needs its whole-number significant_bits")
    try:
        counts = {
            int(index): int(count) for index, count in dict(payload.get("counts") or {}).items()
        }
    except (TypeError, ValueError) as error:
        raise HistogramError(f"the counters are not a map of index to count: {error}") from error
    lowest = payload.get("lowest")
    return Histogram(
        bits,
        max_value=int(payload.get("max_value") or DEFAULT_MAX_VALUE),
        counts=counts,
        total=int(payload.get("total") or 0),
        total_sum=int(payload.get("total_sum") or 0),
        lowest=None if lowest is None else int(lowest),
    )

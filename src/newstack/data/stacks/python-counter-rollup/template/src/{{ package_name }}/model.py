"""Samples, windows and rollups: the vocabulary of a defensible number."""

from __future__ import annotations

import math
from dataclasses import dataclass

VERSION = 1
MICROSECONDS = 1_000_000


class RollupError(ValueError):
    """Something the caller has to fix."""


class Conflict(RollupError):
    """Two rollups disagree about the same shard and window."""

    def __init__(self, shard: str, start_us: int, first: int, second: int) -> None:
        self.shard = shard
        self.start_us = start_us
        super().__init__(
            f"shard {shard} reports {first} and {second} for the window starting "
            f"{start_us}; one of them is wrong, and adding them would be worse"
        )


def _integer(value: object, name: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RollupError(f"{name} must be an integer, got {value!r}")
    if minimum is not None and value < minimum:
        raise RollupError(f"{name} must be at least {minimum}, got {value}")
    return value


@dataclass(frozen=True)
class Sample:
    """One reading of a counter that only ever goes up (until it resets)."""

    at_us: int
    value: int

    def __post_init__(self) -> None:
        _integer(self.at_us, "at_us", minimum=0)
        _integer(self.value, "value", minimum=0)


@dataclass(frozen=True)
class Window:
    """A half-open interval `[start, end)` in microseconds."""

    start_us: int
    end_us: int

    def __post_init__(self) -> None:
        _integer(self.start_us, "start_us", minimum=0)
        _integer(self.end_us, "end_us", minimum=0)
        if self.end_us <= self.start_us:
            raise RollupError(
                f"window end {self.end_us} must be after its start {self.start_us}; "
                "a negative window is how a rate becomes negative"
            )

    @property
    def width_us(self) -> int:
        return self.end_us - self.start_us

    def contains(self, at_us: int) -> bool:
        return self.start_us <= at_us < self.end_us


@dataclass(frozen=True)
class Rollup:
    """What happened in one window, as measured by one shard."""

    name: str
    shard: str
    window: Window
    total: int
    samples: int  # measurement intervals folded in, not raw readings
    resets: int
    first_us: int
    last_us: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise RollupError("name must not be empty")
        if not self.shard.strip():
            raise RollupError("shard must not be empty")
        _integer(self.total, "total", minimum=0)
        _integer(self.samples, "samples", minimum=0)
        _integer(self.resets, "resets", minimum=0)
        if self.samples == 0 and (self.first_us or self.last_us):
            raise RollupError("a rollup with no samples cannot span a time range")
        if self.last_us < self.first_us:
            raise RollupError(
                f"last sample {self.last_us} is before the first {self.first_us}"
            )

    @property
    def covered_us(self) -> int:
        """The time actually observed, summed over the intervals folded in here."""
        if self.samples == 0:
            return 0
        return self.last_us - self.first_us

    def rate_per_second(self) -> float:
        covered = self.covered_us
        if covered == 0:
            raise RollupError(
                f"{self.name} {self.window.start_us}: {self.samples} sample(s) cover no "
                "time, so the only honest rate is unknown, not zero"
            )
        return self.total * MICROSECONDS / covered

    def line(self) -> str:
        try:
            rate = f"{self.rate_per_second():>8.3f}/s"
        except RollupError:
            rate = f"{'unknown':>9}"
        return (
            f"{self.name:<12} {self.shard:<8} {self.window.start_us:>12} "
            f"{self.total:>8} {self.samples:>3} {self.resets:>2} {rate}"
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "shard": self.shard,
            "window": {"start_us": self.window.start_us, "end_us": self.window.end_us},
            "total": self.total,
            "samples": self.samples,
            "resets": self.resets,
            "first_us": self.first_us,
            "last_us": self.last_us,
            "covered_us": self.covered_us,
        }


HEADER = f"{'name':<12} {'shard':<8} {'window':>12} {'total':>8} {'n':>3} {'rst':>2} {'rate':>10}"


def delta_for(previous: Sample, current: Sample) -> tuple[int, bool]:
    """The increase between two readings, and whether the counter restarted."""
    if current.at_us < previous.at_us:
        raise RollupError(
            f"samples arrived out of order: {current.at_us} before {previous.at_us}"
        )
    if current.value < previous.value:
        return current.value, True
    return current.value - previous.value, False


def align(at_us: int, width_us: int) -> int:
    """The start of the window containing an instant: floor, never round."""
    _integer(at_us, "at_us", minimum=0)
    _integer(width_us, "width_us", minimum=1)
    return at_us - at_us % width_us


def window_of(at_us: int, width_us: int) -> Window:
    start = align(at_us, width_us)
    return Window(start_us=start, end_us=start + width_us)


def seconds(value: float) -> int:
    """A human window in seconds, as an integer count of microseconds."""
    if not math.isfinite(value) or value <= 0:
        raise RollupError(f"a window must be a positive number of seconds, got {value!r}")
    return round(value * MICROSECONDS)

"""The two structures the limiter returns: its configuration and its answer."""

from __future__ import annotations

from dataclasses import dataclass

MICROSECONDS = 1_000_000


@dataclass(frozen=True, slots=True)
class Config:
    """`limit` requests per `per_seconds` seconds, with a burst of `capacity`.

    The burst is not a second number to tune: it defaults to the limit, which is what a caller
    means by "100 requests a minute" — a hundred now, then one a second... except that a minute
    is 60 seconds, so one every 0.6 s. That asymmetry is the point of the next class.
    """

    limit: int = 100
    per_seconds: int = 60
    capacity: int | None = None

    def __post_init__(self) -> None:
        if isinstance(self.limit, bool) or not isinstance(self.limit, int) or self.limit < 1:
            raise ValueError(f"limit must be a positive integer, got {self.limit!r}")
        if (
            isinstance(self.per_seconds, bool)
            or not isinstance(self.per_seconds, int)
            or self.per_seconds < 1
        ):
            raise ValueError(f"per_seconds must be a positive integer, got {self.per_seconds!r}")
        if self.capacity is not None:
            if isinstance(self.capacity, bool) or not isinstance(self.capacity, int):
                raise ValueError(f"capacity must be an integer, got {self.capacity!r}")
            if self.capacity < 1:
                raise ValueError(f"capacity must be at least 1, got {self.capacity}")

    @property
    def burst(self) -> int:
        return self.capacity if self.capacity is not None else self.limit


@dataclass(frozen=True, slots=True)
class Decision:
    """One answer, with the arithmetic that produced it made visible."""

    allowed: bool
    key: str
    remaining: int
    retry_after_us: int
    reset_at_us: int
    cost: int

    @property
    def retry_after_s(self) -> float:
        return self.retry_after_us / MICROSECONDS

    @property
    def reset_at_s(self) -> float:
        return self.reset_at_us / MICROSECONDS

    def line(self) -> str:
        verdict = "allow" if self.allowed else "deny "
        if self.allowed:
            tail = f"remaining={self.remaining}"
        else:
            tail = f"retry_after={self.retry_after_s:.3f}s"
        return f"{verdict} {self.key:<12} cost={self.cost} {tail}"

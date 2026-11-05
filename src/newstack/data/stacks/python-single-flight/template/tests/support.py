"""A clock the tests can move, so no test sleeps for a TTL."""

from __future__ import annotations


class Clock:
    def __init__(self, start: float = 0.0) -> None:
        self.value = start

    def now(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds

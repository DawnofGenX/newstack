"""The vocabulary of a cache that cannot stampede."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


class FlightError(RuntimeError):
    """A load failed, and every caller waiting on it is told the same thing."""

    def __init__(self, key: str, error: BaseException) -> None:
        self.key = key
        self.error = error
        super().__init__(f"loading {key!r} failed: {type(error).__name__}: {error}")


class LoadError(ValueError):
    """The caller asked for something the cache cannot do."""


def check_key(key: object) -> str:
    if not isinstance(key, str):
        raise LoadError(f"key must be a string, got {type(key).__name__}")
    if not key.strip():
        raise LoadError("key must not be empty")
    return key


def check_ttl(ttl_s: float | None) -> float | None:
    if ttl_s is None:
        return None
    if isinstance(ttl_s, bool) or not isinstance(ttl_s, (int, float)):
        raise LoadError(f"ttl must be a number of seconds or None, got {ttl_s!r}")
    if ttl_s <= 0:
        raise LoadError(f"ttl must be positive, got {ttl_s!r}")
    return float(ttl_s)


@dataclass
class Entry:
    """One key's state. The event is what a waiter blocks on, and ONLY that."""

    key: str
    event: threading.Event = field(default_factory=threading.Event)
    value: object = None
    error: BaseException | None = None
    ready: bool = False
    expires_at: float | None = None
    loads: int = 0

    def expired(self, now: float) -> bool:
        return self.expires_at is not None and now >= self.expires_at

    def settle(self, value: object, expires_at: float | None) -> None:
        self.value = value
        self.error = None
        self.ready = True
        self.expires_at = expires_at
        self.loads += 1
        self.event.set()

    def fail(self, error: BaseException) -> None:
        self.error = error
        self.ready = True
        self.event.set()


@dataclass
class Stats:
    calls: int = 0
    hits: int = 0
    waits: int = 0
    loads: int = 0
    failures: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "calls": self.calls,
            "hits": self.hits,
            "waits": self.waits,
            "loads": self.loads,
            "failures": self.failures,
        }

    def line(self) -> str:
        return (
            f"{self.calls} call(s): {self.hits} hit(s), {self.waits} waited, "
            f"{self.loads} load(s), {self.failures} failure(s)"
        )

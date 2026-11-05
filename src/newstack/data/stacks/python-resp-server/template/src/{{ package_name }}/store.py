"""The keyspace: a dict with expiry and one lock.

Every command runs under the same lock, which is why the server can hand a
connection to its own thread without a second thought.
"""

from __future__ import annotations

import math
import threading
import time


class NotAnInteger(ValueError):
    """INCR was handed a value that is not a base-10 integer."""


class Store:
    def __init__(self, *, clock=time.monotonic) -> None:
        self._lock = threading.Lock()
        self._data: dict[bytes, tuple[bytes, float | None]] = {}
        self._clock = clock

    # -- helpers ---------------------------------------------------------
    def _live(self, key: bytes, now: float) -> tuple[bytes, float | None] | None:
        """Return the entry, dropping it first if its deadline has passed."""
        entry = self._data.get(key)
        if entry is None:
            return None
        expires = entry[1]
        if expires is not None and expires <= now:
            del self._data[key]
            return None
        return entry

    def _expired(self, now: float) -> list[bytes]:
        return [
            key
            for key, (_, expires) in self._data.items()
            if expires is not None and expires <= now
        ]

    # -- commands --------------------------------------------------------
    def set(self, key: bytes, value: bytes, ttl: float | None = None) -> None:
        with self._lock:
            now = self._clock()
            expires = None if ttl is None else now + ttl
            self._data[key] = (value, expires)

    def get(self, key: bytes) -> bytes | None:
        with self._lock:
            entry = self._live(key, self._clock())
            return None if entry is None else entry[0]

    def delete(self, keys: list[bytes]) -> int:
        with self._lock:
            now = self._clock()
            removed = 0
            for key in keys:
                if self._live(key, now) is not None:
                    del self._data[key]
                    removed += 1
            return removed

    def exists(self, keys: list[bytes]) -> int:
        with self._lock:
            now = self._clock()
            return sum(1 for key in keys if self._live(key, now) is not None)

    def incr(self, key: bytes, delta: int = 1) -> int:
        with self._lock:
            now = self._clock()
            entry = self._live(key, now)
            if entry is None:
                value = 0
                expires = None
            else:
                raw, expires = entry
                try:
                    value = int(raw.decode("ascii"))
                except (UnicodeDecodeError, ValueError) as exc:
                    raise NotAnInteger(raw) from exc
            value += delta
            if not -(2**63) <= value < 2**63:
                raise OverflowError("increment or decrement would overflow")
            self._data[key] = (str(value).encode("ascii"), expires)
            return value

    def dbsize(self) -> int:
        with self._lock:
            now = self._clock()
            for key in self._expired(now):
                del self._data[key]
            return len(self._data)

    def flush(self) -> None:
        with self._lock:
            self._data.clear()

    def type_of(self, key: bytes) -> str:
        with self._lock:
            return "string" if self._live(key, self._clock()) is not None else "none"

    def ttl(self, key: bytes) -> int:
        """Redis' three-way answer: -2 missing, -1 no expiry, else seconds left."""
        with self._lock:
            now = self._clock()
            entry = self._live(key, now)
            if entry is None:
                return -2
            expires = entry[1]
            if expires is None:
                return -1
            return max(0, math.ceil(expires - now))

    def keys(self) -> list[bytes]:
        with self._lock:
            now = self._clock()
            for key in self._expired(now):
                del self._data[key]
            return sorted(self._data)

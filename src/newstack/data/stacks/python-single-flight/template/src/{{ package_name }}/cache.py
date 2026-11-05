"""One loader run per key, and no lock held while the loader runs."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from .model import Entry, FlightError, LoadError, Stats, check_key, check_ttl


@dataclass(frozen=True)
class Answer:
    """What one call got back, and how it got it."""

    key: str
    value: object
    hit: bool
    waited: bool

    def line(self) -> str:
        source = "hit" if self.hit else ("waited" if self.waited else "loaded")
        return f"{self.key:<16} {source:<7} {self.value!r}"


class SingleFlight:
    """A TTL cache where concurrent misses for one key run the loader once.

    Two locks, on purpose: `_registry` guards the dictionary for the time it takes
    to look a key up, and each entry carries its own event so waiters block on the
    key they asked for. Holding one lock across the load would serialise every key
    behind the slowest one — a cache with a queue in front of it.
    """

    def __init__(
        self,
        loader: Callable[[str], object],
        *,
        ttl_s: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not callable(loader):
            raise LoadError("loader must be callable")
        self._loader = loader
        self._ttl = check_ttl(ttl_s)
        self._clock = clock
        self._registry = threading.Lock()
        self._entries: dict[str, Entry] = {}
        self.stats = Stats()
        self._counter_lock = threading.Lock()

    def _count(self, field: str) -> None:
        with self._counter_lock:
            setattr(self.stats, field, getattr(self.stats, field) + 1)

    def get(self, key: str) -> Answer:
        name = check_key(key)
        self._count("calls")
        leader = False
        with self._registry:
            entry = self._entries.get(name)
            now = self._clock()
            if entry is not None and entry.ready and not entry.expired(now):
                self._count("hits")
                return Answer(key=name, value=entry.value, hit=True, waited=False)
            if entry is None or (entry.ready and entry.expired(now)):
                entry = Entry(key=name)
                self._entries[name] = entry
                leader = True
            # A ready-but-expired entry is replaced by a fresh one, so a waiter
            # never blocks on a load that already finished.
        if not leader:
            self._count("waits")
            entry.event.wait()
            if entry.error is not None:
                raise FlightError(name, entry.error)
            return Answer(key=name, value=entry.value, hit=True, waited=True)

        self._count("loads")
        try:
            value = self._loader(name)
        except BaseException as error:
            self._count("failures")
            entry.fail(error)
            with self._registry:
                if self._entries.get(name) is entry:
                    del self._entries[name]
            # Every caller sees one exception type, leader included: the loader's own
            # error would otherwise make callers catch ConnectionError in one path and
            # FlightError in the other. The original rides along as `.error`.
            raise FlightError(name, error) from error
        # The TTL starts when the value became readable, not when the load began:
        # a loader slower than its own TTL would otherwise produce entries that
        # expire before a single caller reads them.
        started = self._clock()
        expires = None if self._ttl is None else started + self._ttl
        entry.settle(value, expires)
        return Answer(key=name, value=value, hit=False, waited=False)

    def peek(self, key: str) -> Answer | None:
        """Look without loading: a monitoring read must not start work."""
        name = check_key(key)
        with self._registry:
            entry = self._entries.get(name)
            if entry is None or not entry.ready or entry.expired(self._clock()):
                return None
            return Answer(key=name, value=entry.value, hit=True, waited=False)

    def forget(self, key: str) -> bool:
        name = check_key(key)
        with self._registry:
            return self._entries.pop(name, None) is not None

    def clear(self) -> None:
        with self._registry:
            self._entries.clear()

    def __len__(self) -> int:
        with self._registry:
            return len(self._entries)


def call_many(cache: SingleFlight, keys: list[str]) -> list[Answer]:
    """Call the cache once per key, in order, collecting answers or errors."""
    answers: list[Answer] = []
    for key in keys:
        answers.append(cache.get(key))
    return answers

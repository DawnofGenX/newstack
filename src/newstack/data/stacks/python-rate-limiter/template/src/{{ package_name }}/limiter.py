"""The keyed limiter: one lock, one integer per key, and a way to forget idle keys."""

from __future__ import annotations

import threading
from dataclasses import dataclass

from .clock import Monotonic
from .gcra import Gcra
from .model import Config, Decision


@dataclass
class Counters:
    checks: int = 0
    allowed: int = 0
    denied: int = 0
    evicted: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "checks": self.checks,
            "allowed": self.allowed,
            "denied": self.denied,
            "evicted": self.evicted,
        }


class Limiter:
    """A rate limit per key, with the clock injected and the state pruned.

    The lock is coarse on purpose: `check()` is a few integer operations, so a per-key lock
    would cost more than it saves and would make the "no key is starved" test hard to write.
    """

    def __init__(
        self,
        config: Config | None = None,
        clock: object | None = None,
        *,
        max_keys: int | None = None,
        prune_every: int = 256,
    ) -> None:
        if max_keys is not None and max_keys < 1:
            raise ValueError(f"max_keys must be at least 1, got {max_keys}")
        if prune_every < 1:
            raise ValueError(f"prune_every must be at least 1, got {prune_every}")
        self.config = config or Config()
        self.clock = clock or Monotonic()
        self.max_keys = max_keys
        self.prune_every = prune_every
        self._states: dict[str, Gcra] = {}
        self._lock = threading.Lock()
        self._counters = Counters()

    def check(self, key: str, cost: int = 1) -> Decision:
        """Ask the limiter about one key; the answer is a decision, not an exception."""
        if not isinstance(key, str) or not key:
            raise ValueError(f"key must be a non-empty string, got {key!r}")
        now = self.clock.now_us()
        with self._lock:
            state = self._states.get(key)
            if state is None:
                state = Gcra(self.config, now)
                self._states[key] = state
            decision = state.check(key, now, cost)
            self._counters.checks += 1
            if decision.allowed:
                self._counters.allowed += 1
            else:
                self._counters.denied += 1
            # Pruning on a schedule, not on every write: a full scan per request would turn an
            # O(1) answer into an O(keys) one. `max_keys` still gets enforced every time.
            if self.max_keys is not None or self._counters.checks % self.prune_every == 0:
                self._counters.evicted += self._prune_locked(now)
            return decision

    def wait_time_us(self, key: str, cost: int = 1) -> int:
        """How long a caller would have to wait, without spending anything."""
        now = self.clock.now_us()
        with self._lock:
            state = self._states.get(key)
            if state is None:
                return 0
            return state.check(key, now, cost).retry_after_us

    def prune(self) -> int:
        """Drop the keys whose state has refilled completely; returns how many went."""
        now = self.clock.now_us()
        with self._lock:
            removed = self._prune_locked(now)
            self._counters.evicted += removed
            return removed

    def _prune_locked(self, now_us: int) -> int:
        evicted = 0
        for key in [name for name, state in self._states.items() if state.idle(now_us)]:
            del self._states[key]
            evicted += 1
        if self.max_keys is not None:
            while len(self._states) > self.max_keys:
                # A full table with no idle key means the limit is too high for the key space;
                # dropping the key that refilled soonest is the least surprising answer.
                oldest = min(self._states.items(), key=lambda item: item[1].tat_us)
                del self._states[oldest[0]]
                evicted += 1
        return evicted

    def stats(self) -> dict[str, int]:
        with self._lock:
            payload = self._counters.as_dict()
            payload["keys"] = len(self._states)
            return payload

    def __len__(self) -> int:
        with self._lock:
            return len(self._states)

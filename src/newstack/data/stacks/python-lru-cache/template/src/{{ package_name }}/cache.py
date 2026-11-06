"""Four replacement policies, one interface: `access(key)` returns whether it hit.

A cache used as a *simulation* never stores a value. What decides its hit ratio is
only the bookkeeping: which key a policy forgets. Keeping that separate is what
makes the policies comparable, and it is why every class here counts its own work
(hits, misses, evictions, and the extra scans or promotions that buy the result).
"""

from __future__ import annotations

from collections import OrderedDict


class CacheError(ValueError):
    """A cache that cannot be built with the capacity or key it was given."""


class Cache:
    """The interface every policy implements."""

    name = "cache"

    def __init__(self, capacity: int) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise CacheError(f"a capacity is a whole number, not {capacity!r}")
        if capacity < 1:
            raise CacheError(f"a cache needs room for at least one key, not {capacity}")
        self.capacity = capacity
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.scans = 0
        self.promotions = 0

    def access(self, key: str) -> bool:
        """Record one access; return True when the key was already resident."""
        raise NotImplementedError

    def resident(self) -> set[str]:
        """The keys currently held, for tests that want to look inside."""
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    @property
    def accesses(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        total = self.accesses
        return self.hits / total if total else 0.0

    def _touch(self, key: str) -> None:
        if isinstance(key, str) is False:
            raise CacheError(f"a key is a string, not {type(key).__name__}")

    def _record(self, hit: bool) -> bool:
        if hit:
            self.hits += 1
        else:
            self.misses += 1
        return hit


class Fifo(Cache):
    """Forget the key that has been resident longest, no matter how often it is used."""

    name = "fifo"

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self._order: dict[str, None] = {}

    def __len__(self) -> int:
        return len(self._order)

    def resident(self) -> set[str]:
        return set(self._order)

    def access(self, key: str) -> bool:
        self._touch(key)
        if key in self._order:
            return self._record(True)
        if len(self._order) >= self.capacity:
            oldest = next(iter(self._order))
            del self._order[oldest]
            self.evictions += 1
        self._order[key] = None
        return self._record(False)


class Lru(Cache):
    """Forget the key used least recently."""

    name = "lru"

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self._order: OrderedDict[str, None] = OrderedDict()

    def __len__(self) -> int:
        return len(self._order)

    def resident(self) -> set[str]:
        return set(self._order)

    def access(self, key: str) -> bool:
        self._touch(key)
        if key in self._order:
            self._order.move_to_end(key)
            return self._record(True)
        if len(self._order) >= self.capacity:
            self._order.popitem(last=False)
            self.evictions += 1
        self._order[key] = None
        return self._record(False)


class Clock(Cache):
    """Approximate LRU with one reference bit per slot and a hand that sweeps.

    A hit only sets a bit; an eviction sweeps the hand, clearing bits it passes and
    taking the first slot whose bit is already clear. That is why it costs a few
    scans instead of a list reordering - and why `scans` is counted.
    """

    name = "clock"

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity)
        self._slots: list[str | None] = [None] * capacity
        self._bits: list[int] = [0] * capacity
        self._index: dict[str, int] = {}
        self._hand = 0

    def __len__(self) -> int:
        return len(self._index)

    def resident(self) -> set[str]:
        return set(self._index)

    def access(self, key: str) -> bool:
        self._touch(key)
        slot = self._index.get(key)
        if slot is not None:
            self._bits[slot] = 1
            return self._record(True)
        if len(self._index) >= self.capacity:
            while True:
                self.scans += 1
                victim = self._hand
                if self._bits[victim] == 1:
                    self._bits[victim] = 0
                    self._hand = (self._hand + 1) % self.capacity
                    continue
                break
            old = self._slots[victim]
            if old is not None:
                del self._index[old]
                self.evictions += 1
            slot = victim
            self._hand = (self._hand + 1) % self.capacity
        else:
            slot = next(number for number, value in enumerate(self._slots) if value is None)
        self._slots[slot] = key
        self._bits[slot] = 1
        self._index[key] = slot
        return self._record(False)


class SegmentedLru(Cache):
    """A small probation area in front of a protected area.

    A key that is used while on probation is promoted; protected evictions demote
    into probation instead of leaving. A sequential scan therefore only ever fills
    the probation area, and the working set it would otherwise flush stays put.
    """

    name = "slru"

    def __init__(self, capacity: int, protected_share: float = 0.8) -> None:
        super().__init__(capacity)
        if not 0.0 < protected_share < 1.0:
            raise CacheError(f"a protected share is a fraction in (0, 1), not {protected_share}")
        self.protected_capacity = max(1, int(capacity * protected_share))
        self.probation_capacity = capacity - self.protected_capacity
        self._probation: OrderedDict[str, None] = OrderedDict()
        self._protected: OrderedDict[str, None] = OrderedDict()

    def __len__(self) -> int:
        return len(self._probation) + len(self._protected)

    def resident(self) -> set[str]:
        return set(self._probation) | set(self._protected)

    def _evict_probation(self) -> str:
        key, _ = self._probation.popitem(last=False)
        self.evictions += 1
        return key

    def _shrink_protected(self) -> None:
        while len(self._protected) > self.protected_capacity:
            demoted, _ = self._protected.popitem(last=False)
            self._probation[demoted] = None
            self.promotions += 1

    def access(self, key: str) -> bool:
        self._touch(key)
        if key in self._protected:
            self._protected.move_to_end(key)
            return self._record(True)
        if key in self._probation:
            del self._probation[key]
            self._protected[key] = None
            self.promotions += 1
            self._shrink_protected()
            return self._record(True)
        if len(self) >= self.capacity:
            if self._probation:
                self._evict_probation()
            else:
                self._protected.popitem(last=False)
                self.evictions += 1
        self._probation[key] = None
        self._shrink_protected()
        return self._record(False)


POLICIES: dict[str, type[Cache]] = {
    "fifo": Fifo,
    "lru": Lru,
    "clock": Clock,
    "slru": SegmentedLru,
}


def by_name(name: str) -> type[Cache]:
    """The policy class for a name, with the list of names it could have meant."""
    chosen = POLICIES.get(name)
    if chosen is None:
        known = ", ".join(sorted(POLICIES))
        raise CacheError(f"unknown policy {name!r}; known policies are {known}")
    return chosen

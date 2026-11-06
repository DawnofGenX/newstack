"""The heap itself: a heap that never compares keys, buckets follow the bits.

Integer keys fall into a bucket per bucket, chosen by how many bits
separate a key from the base the window stands on. Pop-min reads the
buckets in order and never asks which of two keys is smaller: bucket
order IS key order for keys inside the window. A push that steps below
the base leaves the window, and the honest answer is a rebuild, not a
lie about the cost.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

BUCKETS = 65


class HeapError(ValueError):
    """The keys stepped outside what a radix window can hold."""


def bucket_of(key: int, base: int) -> int:
    """How many bits separate the key from the base.

    The bucket is the position of the highest bit where the two differ,
    plus one; a key equal to the base sits in bucket zero.
    """
    return (key ^ base).bit_length()


@dataclass(frozen=True)
class Edit:
    """What one op cost: where the key landed, whether the heap rebuilt."""

    op: str
    bucket: int
    rebuilt: bool

    def line(self) -> str:
        return f"{self.op} bucket {self.bucket} rebuilt={self.rebuilt}"


class RadixHeap:
    """An integer min-heap whose tree shape is the keys' bits.

    Keys wait in 65 bucket lists; bucket ``j`` holds exactly the keys
    whose highest differing bit from the base sits at ``j - 1``. The
    base never walks back inside the window, so a monotone stream --
    every push at or above the last pop -- spends no full rebuild at
    all. A backwards push leaves the window and buys one rebuild.
    """

    def __init__(self) -> None:
        self._buckets: list[list[tuple[int, object]]] = [[] for _ in range(BUCKETS)]
        self._base = 0
        self._size = 0
        self._rebuilds = 0
        self._empties = 0

    # -- the window -----------------------------------------------------

    @property
    def base(self) -> int:
        """The key the window stands on: the last pop, or zero."""
        return self._base

    @property
    def rebuilds(self) -> int:
        """Full rebuilds spent, every one paid by a backwards push."""
        return self._rebuilds

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return self._size > 0

    def __iter__(self) -> Iterator[int]:
        return self.pop_all()

    # -- the ops ----------------------------------------------------------

    def push(self, key: int, value: object = None) -> Edit:
        """Drop a key in its bucket; a backwards key buys one rebuild.

        The fallback for a non-monotone stream is honest: the window
        resets under the new key and every held key is refiled, so the
        answer survives -- only the cost is one full rebuild extra.
        """
        key = _as_key(key)
        if key < self._base:
            self._base = key
            self._rebuilds += 1
            self._refile()
            self._buckets[0].append((key, value))
            self._size += 1
            return Edit("push", 0, True)
        bucket = bucket_of(key, self._base)
        self._buckets[bucket].append((key, value))
        self._size += 1
        return Edit("push", bucket, False)

    def pop(self) -> tuple[int, object]:
        """The smallest key, found by reading buckets, never by comparing.

        The window advances onto the answer and everything that was in
        front of it falls to lower buckets -- never sideways.
        """
        if self._size == 0:
            raise HeapError("the heap holds nothing")
        self._empties = 0
        front = self._buckets[0]
        if front:
            key, value = front.pop(0)
            self._size -= 1
            return key, value
        index = 1
        while not self._buckets[index]:
            self._empties += 1
            index += 1
        bucket = self._buckets[index]
        spot = min(range(len(bucket)), key=lambda i: bucket[i][0])
        key, value = bucket.pop(spot)
        self._size -= 1
        self._base = key
        self._refile()
        return key, value

    def pop_all(self) -> Iterator[int]:
        """Drain in sorted order -- the promise of every radix heap."""
        while self._size:
            yield self.pop()[0]

    def peek(self) -> tuple[int, object]:
        """The next pop, without paying for it."""
        if self._size == 0:
            raise HeapError("the heap holds nothing")
        front = self._buckets[0]
        if front:
            return min(front, key=lambda entry: entry[0])
        for bucket in self._buckets[1:]:
            if bucket:
                return min(bucket, key=lambda entry: entry[0])
        raise HeapError("the heap counts keys it does not hold")

    def entries(self) -> list[tuple[int, object]]:
        """Every pair held, in the order the buckets read them."""
        held: list[tuple[int, object]] = []
        for bucket in self._buckets:
            held.extend(bucket)
        return held

    # -- the invariants -----------------------------------------------------

    def invariant(self) -> bool:
        """Every held key sits at its bit-length-from-base bucket.

        Bucket zero is the base itself; a key below the base has no
        bucket that keeps the window honest, so none may hide there.
        """
        if len(self._buckets) != BUCKETS:
            return False
        for index, bucket in enumerate(self._buckets):
            for key, _ in bucket:
                if bucket_of(key, self._base) != index:
                    return False
        return True

    def rebuild(self) -> None:
        """Reset the window under zero and refile every key."""
        self._base = 0
        self._refile()

    def _refile(self) -> None:
        """Move every held key to the bucket its bits ask for."""
        held = self.entries()
        self._buckets = [[] for _ in range(BUCKETS)]
        self._size = 0
        for key, value in held:
            self._buckets[bucket_of(key, self._base)].append((key, value))
            self._size += 1

    def stats(self) -> dict:
        """A snapshot of the window, for reports that must not lie."""
        return {
            "size": self._size,
            "base": self._base,
            "rebuilds": self._rebuilds,
            "empties": self._empties,
            "buckets": [len(bucket) for bucket in self._buckets],
            "nonzero": sum(1 for bucket in self._buckets if bucket),
            "invariant": self.invariant(),
        }

    def lines(self) -> list[str]:
        """A report of the shape: where the keys sit, and what it cost."""
        stats = self.stats()
        rows = [f"size {stats['size']} base {stats['base']} rebuilds {stats['rebuilds']}"]
        for index, count in enumerate(stats["buckets"]):
            if count:
                rows.append(f"  bucket {index:>2}  {'*' * count}")
        return rows


def _as_key(key: object) -> int:
    if isinstance(key, bool) or not isinstance(key, int):
        raise HeapError(f"a key must be a whole number, got {key!r}")
    if key < 0:
        raise HeapError(f"the window floors at zero, {key} sits below it")
    if key.bit_length() >= BUCKETS:
        raise HeapError(f"a key of {key.bit_length()} bits does not fit {BUCKETS} buckets")
    return key

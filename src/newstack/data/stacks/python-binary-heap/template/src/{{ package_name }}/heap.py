"""A min-heap over integer keys, hand-rolled on a plain list.

The parent rides no higher than its children, and the promise is
checked, never assumed: the shipped checker in oracle.py walks the
array after every operation, and the drain order of any push/pop
storm must equal the plain `sorted(pushed)` exactly. No heapq, no
cleverness — sift-up swaps a rising key with its parent, sift-down
hands each slot to its smaller child, both on a plain Python list.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .keys import ensure_key
from .oracle import heap_breaks


class HeapError(ValueError):
    """The heap is asked for something it does not hold."""


def _sift_up(array: list[int], slot: int) -> None:
    """Walk a fresh key up until its parent rides no higher."""
    while slot > 0:
        parent = (slot - 1) // 2
        if array[parent] <= array[slot]:
            break
        array[parent], array[slot] = array[slot], array[parent]
        slot = parent


def _sift_down(array: list[int], slot: int) -> None:
    """Hand a sunk slot down to its smaller child until it rests."""
    size = len(array)
    while True:
        left = 2 * slot + 1
        if left >= size:
            break
        pick = left
        right = left + 1
        if right < size and array[right] < array[left]:
            pick = right
        if array[slot] <= array[pick]:
            break
        array[slot], array[pick] = array[pick], array[slot]
        slot = pick


class MinHeap:
    """Integer keys in a plain list; the parent rides no higher than its children."""

    __slots__ = ("_array",)

    def __init__(self, keys: Any = ()) -> None:
        self._array: list[int] = []
        for key in keys:
            self.push(key)

    def push(self, key: int) -> None:
        """Seat a key at the end and sift it up to its resting slot."""
        self._array.append(ensure_key(key))
        _sift_up(self._array, len(self._array) - 1)

    def pop(self) -> int:
        """Hand over the smallest key; empty is refused, never zero."""
        if not self._array:
            raise HeapError("the heap is empty")
        top = self._array[0]
        last = self._array.pop()
        if self._array:
            self._array[0] = last
            _sift_down(self._array, 0)
        return top

    def peek(self) -> int:
        """The smallest key, which is the array's head, or refused."""
        if not self._array:
            raise HeapError("the heap is empty")
        return self._array[0]

    def drain(self) -> list[int]:
        """Pop until empty: the order the storm's answers must equal."""
        out: list[int] = []
        while self._array:
            out.append(self.pop())
        return out

    def array(self) -> list[int]:
        """The array as it stands — shape and all, for the checker."""
        return list(self._array)

    def breaks(self) -> list[int]:
        """Slots where the parent rule broke; honest means empty."""
        return heap_breaks(self._array)

    def __len__(self) -> int:
        return len(self._array)

    def __bool__(self) -> bool:
        return bool(self._array)

    def __iter__(self) -> Iterator[int]:
        return iter(self.drain())

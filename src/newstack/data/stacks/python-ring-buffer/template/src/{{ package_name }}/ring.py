"""The fixed-capacity FIFO: the cursor never leaves the ring.

A ring buffer seats integer values in a closed set of slots. The
read cursor and the count are the whole state; the logical contents
are recomputed from `(head, count)` after every operation, never
carried over. An over-capacity push drops the oldest value: the write
lands exactly on the oldest slot, at `tail == head`, and the cursor
steps past it. This module owns the phrase *the cursor never leaves
the ring* — the registry detector reads it from here, nowhere else.
"""

from __future__ import annotations

from .values import ensure_value


class RingError(ValueError):
    """The buffer was asked for something its slots cannot give."""


class RingBuffer:
    """A fixed-capacity FIFO over integers with a drop-oldest policy."""

    __slots__ = ("_capacity", "_count", "_head", "_slots", "overwrites")

    def __init__(self, capacity: int, values: object = ()) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
            raise RingError(f"no ring of {capacity!r}: capacity is a positive integer")
        self._capacity = capacity
        self._slots: list[int] = [0] * capacity
        self._head = 0
        self._count = 0
        self.overwrites = 0
        for candidate in values:  # type: ignore[union-attr]
            self.push(candidate)

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def head(self) -> int:
        return self._head

    def __len__(self) -> int:
        return self._count

    @property
    def full(self) -> bool:
        return self._count == self._capacity

    @property
    def tail(self) -> int:
        """The slot the next push writes; on a full ring, the oldest slot."""
        return (self._head + self._count) % self._capacity

    def push(self, candidate: object) -> int | None:
        """Seat a value; on a full ring the oldest is overwritten, return it."""
        value = ensure_value(candidate)
        dropped = None
        if self._count == self._capacity:
            dropped = self._slots[self.tail]
            self._slots[self.tail] = value
            self._head = (self._head + 1) % self._capacity
            self.overwrites += 1
        else:
            self._slots[self.tail] = value
            self._count += 1
        return dropped

    def pop(self) -> int:
        """Hand back the oldest value and step the cursor over it."""
        if not self._count:
            raise RingError("the buffer is empty: nothing to pop")
        value = self._slots[self._head]
        self._slots[self._head] = 0
        self._head = (self._head + 1) % self._capacity
        self._count -= 1
        return value

    def peek(self) -> int:
        """The oldest value, the cursor unmoved."""
        if not self._count:
            raise RingError("the buffer is empty: nothing to peek")
        return self._slots[self._head]

    def contents(self) -> tuple[int, ...]:
        """The walk: logical contents recomputed from (head, count)."""
        return tuple(
            self._slots[(self._head + step) % self._capacity]
            for step in range(self._count)
        )

    def drain(self) -> list[int]:
        """Everything, in order, leaving an empty buffer behind."""
        seen = list(self.contents())
        self._slots = [0] * self._capacity
        self._head = 0
        self._count = 0
        return seen

    def invariant(self) -> bool:
        """Every promise the slots make about the cursor and the count."""
        return (
            0 <= self._head < self._capacity
            and 0 <= self.tail < self._capacity
            and 0 <= self._count <= self._capacity
        )

    def audit(self) -> list[str]:
        """The named breaks at this position; empty means clean."""
        faults: list[str] = []
        if not 0 <= self._head < self._capacity:
            faults.append(f"head {self._head} outside 0..{self._capacity - 1}")
        if not 0 <= self.tail < self._capacity:
            faults.append(f"tail {self.tail} outside 0..{self._capacity - 1}")
        if not 0 <= self._count <= self._capacity:
            faults.append(f"count {self._count} past capacity {self._capacity}")
        if self.full and self.tail != self._head:
            faults.append("a full ring writes past the oldest")
        return faults

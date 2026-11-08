"""Deque: a double-ended queue, both ends open.

The rule this deque keeps, and the marker the detector looks for:
both ends are first-class. An append or pop at either end is O(1) in
spirit; rotate shifts every item by one step without losing any.
The deque answers its contents in order, left to right. Mutate the
shift direction and the rotation lands on the wrong neighbour.

Detect phrase: both ends are first-class, and a rotation never loses an item.
"""
from __future__ import annotations

MAX_CAPACITY = 100


class DequeError(ValueError):
    """An operation the deque refuses."""

    __slots__ = ()


class Deque:
    """A small, honest double-ended queue."""

    __slots__ = ("_items",)

    def __init__(self, values=()) -> None:
        self._items = list(values)
        if len(self._items) > MAX_CAPACITY:
            raise DequeError(f"capacity exceeded {MAX_CAPACITY}")

    def append(self, value: int) -> None:
        if len(self._items) >= MAX_CAPACITY:
            raise DequeError(f"capacity exceeded {MAX_CAPACITY}")
        self._items.append(value)

    def appendleft(self, value: int) -> None:
        if len(self._items) >= MAX_CAPACITY:
            raise DequeError(f"capacity exceeded {MAX_CAPACITY}")
        self._items.insert(0, value)

    def pop(self):
        if not self._items:
            raise DequeError("pop from empty deque")
        return self._items.pop()

    def popleft(self):
        if not self._items:
            raise DequeError("pop from empty deque")
        return self._items.pop(0)

    def peek(self):
        if not self._items:
            raise DequeError("peek empty deque")
        return self._items[-1]

    def peekleft(self):
        if not self._items:
            raise DequeError("peek empty deque")
        return self._items[0]

    def rotate(self, steps: int = 1) -> None:
        if not self._items:
            return
        n = len(self._items)
        steps %= n
        if steps:
            self._items = self._items[-steps:] + self._items[:-steps]

    def to_list(self) -> list:
        return list(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)


def _validate_value(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DequeError("value must be an integer")
    return value


def make_deque(values=()) -> Deque:
    if not isinstance(values, (list, tuple)):
        raise DequeError("values must be a list or tuple")
    out = [ _validate_value(v) for v in values]
    return Deque(out)


def append(d: Deque, value) -> Deque:
    d.append(_validate_value(value))
    return d


def append_left(d: Deque, value) -> Deque:
    d.appendleft(_validate_value(value))
    return d


def pop(d: Deque):
    return d.pop()


def pop_left(d: Deque):
    return d.popleft()


def peek(d: Deque):
    return d.peek()


def peek_left(d: Deque):
    return d.peekleft()


def rotate(d: Deque, steps: int = 1) -> Deque:
    if not isinstance(steps, int) or isinstance(steps, bool):
        raise DequeError("steps must be an integer")
    d.rotate(steps)
    return d


def to_list(d: Deque) -> list:
    return d.to_list()


def audit_deque(d: Deque, oracle: list) -> bool:
    return d.to_list() == list(oracle)


__all__ = [
    "MAX_CAPACITY",
    "Deque",
    "DequeError",
    "append",
    "append_left",
    "audit_deque",
    "make_deque",
    "peek",
    "peek_left",
    "pop",
    "pop_left",
    "rotate",
    "to_list",
]

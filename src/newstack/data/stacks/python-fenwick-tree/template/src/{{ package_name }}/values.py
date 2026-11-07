"""Which values a tree accepts, and how they render.

A Fenwick tree sums integers, so a value that is not a whole number has
no place in a cell or a delta; it is refused at the door rather than
quietly coerced into an answer that would not survive the next add.
"""

from __future__ import annotations


class ValueRejection(ValueError):
    """The value cannot stand in a cell or ride an add."""


def ensure_value(value: object) -> int:
    """Return the whole number the caller meant, or refuse the stand-in."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueRejection(f"a tree sums whole numbers, got {value!r}")
    return value


def describe(value: object) -> str:
    """Render a value the way a report would name it."""
    return str(value)


def step_size(index: int) -> int:
    """The lowest set bit of a cell index -- the arithmetic values own."""
    if not isinstance(index, int) or isinstance(index, bool) or index < 1:
        raise ValueRejection(f"only a cell index from one up has a step, got {index!r}")
    return index & -index

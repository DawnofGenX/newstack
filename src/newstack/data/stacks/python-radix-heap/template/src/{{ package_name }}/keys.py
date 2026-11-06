"""Which keys a radix window accepts, and how they render.

A radix heap walks bits, so the order it answers in is the order of
whole numbers; anything that is not one is refused at the door rather
than quietly reordered later.
"""

from __future__ import annotations


class KeyValueError(ValueError):
    """The value cannot stand in a bucket."""


def ensure_key(key: object) -> int:
    """Return the whole number the caller meant, or refuse the stand-in."""
    if isinstance(key, bool) or not isinstance(key, int):
        raise KeyValueError(f"a radix window walks whole numbers, got {key!r}")
    return key


def describe(key: object) -> str:
    """Render a key the way the buckets would name it."""
    return str(key)


def seat_of(key: int, base: int) -> int:
    """The bucket a key takes under a base -- the keys module's arithmetic."""
    if not isinstance(key, int) or isinstance(key, bool):
        raise KeyValueError(f"only whole numbers take a seat, got {key!r}")
    return (key ^ base).bit_length()

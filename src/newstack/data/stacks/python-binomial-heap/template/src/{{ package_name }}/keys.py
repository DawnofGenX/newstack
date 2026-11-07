"""Which keys a forest accepts, and how they render.

A binomial heap compares keys to keep its roots ordered, so the whole
numbers may be negative -- unlike a windowed heap, no key is outside
the shape. Anything that is not a whole number is refused at the door.
"""

from __future__ import annotations


class KeyValueError(ValueError):
    """The value cannot stand in a tree."""


def ensure_key(key: object) -> int:
    """Return the whole number the caller meant, or refuse the stand-in."""
    if isinstance(key, bool) or not isinstance(key, int):
        raise KeyValueError(f"a forest orders whole numbers, got {key!r}")
    return key


def describe(key: object) -> str:
    """Render a key the way the roots would name it."""
    return str(key)


def bits(size: int) -> str:
    """The shape a count claims: its binary digits, most significant first."""
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise KeyValueError(f"a forest counts whole keys, got {size!r}")
    return bin(size)[2:]

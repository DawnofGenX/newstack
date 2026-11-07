"""The gate: bounded integers in, keys out, whole or not at all.

A key is one bounded integer. The gate refuses halves, floats, floats
pretending to be ints, booleans, and values past the edge, so keys
reach the tree whole or never arrive.
"""

from __future__ import annotations

MAX_KEY = 10**9


class KeyError(ValueError):
    """A candidate is no key at all."""

    __slots__ = ()


def ensure_key(value: object) -> int:
    """Return the validated integer; refuse everything else by name."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise KeyError(f"not a key: {value!r} is not an integer")
    if abs(value) > MAX_KEY:
        raise KeyError(f"not a key: {value} is past the edge")
    return value


def describe_key(key: int) -> str:
    """The display form of a key, printed the way the CLI prints it."""
    return str(ensure_key(key))

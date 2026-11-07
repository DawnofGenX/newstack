"""The key gate: signed 32-bit integers, and nothing else.

A tree is only as honest as the keys it is fed, so the gate keeps
floats, strings, booleans, and oversized values out before any node
is seated. The rules are few and every refusal is named.
"""

from __future__ import annotations

MAX_KEY = 2**31 - 1


class KeysError(ValueError):
    """A candidate is no key at all."""


def ensure_key(candidate: object) -> int:
    """Return the validated key; anything but an int is refused."""
    if isinstance(candidate, bool) or not isinstance(candidate, int):
        raise KeysError(f"not a key: {candidate!r} is not an integer")
    if abs(candidate) > MAX_KEY:
        raise KeysError(f"not a key: {candidate} is past {MAX_KEY}")
    return candidate


def describe(key: int) -> str:
    """The display form of a key, the way the CLI prints it."""
    return str(key)

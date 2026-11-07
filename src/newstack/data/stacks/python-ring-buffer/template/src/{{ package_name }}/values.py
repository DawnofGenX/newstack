"""The value gate: signed 32-bit integers, and nothing else.

A buffer is only as honest as the values it is fed, so the gate
keeps floats, strings, booleans, and oversized values out before any
slot is written. The rules are few and every refusal is named.
"""

from __future__ import annotations

MAX_VALUE = 2**31 - 1


class ValuesError(ValueError):
    """A candidate is no value at all."""


def ensure_value(candidate: object) -> int:
    """Return the validated value; anything but an int is refused."""
    if isinstance(candidate, bool) or not isinstance(candidate, int):
        raise ValuesError(f"not a value: {candidate!r} is not an integer")
    if abs(candidate) > MAX_VALUE:
        raise ValuesError(f"not a value: {candidate} is past {MAX_VALUE}")
    return candidate


def describe(value: int) -> str:
    """The display form of a value, the way the CLI prints it."""
    return str(value)

"""The fixed integer domain: 0 through 255, and nothing else.

A Bloom filter over ``[0, 256)`` can only promise what its domain
lets it promise, so the gate keeps every other object out before a
single bit is written — negatives, 256, booleans, strings. The
universe is small on purpose: it is small enough that the shipped
audit can answer for *every* key in it, key by key, and the claim
"in the shipped configs, no absent key answers present" is a
finished computation, not a hope.
"""

from __future__ import annotations

UNIVERSE = 256


class UniverseError(ValueError):
    """A candidate is no key of the universe."""


def ensure_key(candidate: object) -> int:
    """Return the validated key; anything outside [0, UNIVERSE) fails."""
    if isinstance(candidate, bool) or not isinstance(candidate, int):
        raise UniverseError(f"no key: {candidate!r} is not an integer")
    if not 0 <= candidate < UNIVERSE:
        raise UniverseError(f"no key: {candidate} leaves [0, {UNIVERSE})")
    return candidate


def parse_key(text: object) -> int:
    """The gate for command-line text: digits in, key out."""
    if not isinstance(text, str) or not text.isdecimal():
        raise UniverseError(f"no key: {text!r} is not a decimal integer")
    return ensure_key(int(text))


def ensure_seed(candidate: object) -> int:
    """Return the validated seed; seeds are non-negative integers."""
    if isinstance(candidate, bool) or not isinstance(candidate, int):
        raise UniverseError(f"no seed: {candidate!r} is not an integer")
    if candidate < 0:
        raise UniverseError(f"no seed: {candidate} is negative")
    return candidate


def describe(value: int) -> str:
    """The display form of a key, padded so columns hold."""
    return f"{value:>3}"

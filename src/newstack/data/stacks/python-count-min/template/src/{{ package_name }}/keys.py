"""The key gate: integers on the fixed universe, and nothing else.

The sketch is only as honest as the keys it is fed, so the gate
keeps negatives, universe-sized values, floats, and strings out
before a single cell is touched. The universe is fixed at [0, 256):
every key is one byte, and every refusal is named.
"""

from __future__ import annotations

UNIVERSE = 256
MAX_KEY = UNIVERSE - 1


class KeysError(ValueError):
    """A candidate is no key at all."""


def ensure_key(candidate: object) -> int:
    """Return the validated key; anything off the universe is refused."""
    if isinstance(candidate, bool) or not isinstance(candidate, int):
        raise KeysError(f"not a key: {candidate!r} is not an integer")
    if not 0 <= candidate < UNIVERSE:
        raise KeysError(f"not a key: {candidate} is off [0, {UNIVERSE})")
    return candidate


def describe(key: int) -> str:
    """The display form of a key, the way the CLI prints it."""
    return str(key)

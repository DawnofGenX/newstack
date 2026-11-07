"""The key gate: integers inside [0, 256), and nothing else.

The universe of this tree is fixed and small on purpose: eight bits,
two hundred fifty-six seats. A query or a stored key outside the
universe is refused by name before any cluster is touched, so a
silent truncation can never masquerade as an answer.
"""

from __future__ import annotations

MIN_KEY = 0
MAX_KEY = 255
UNIVERSE = MAX_KEY + 1          # 256 seats, eight bits, fixed


class KeysError(ValueError):
    """A candidate is no key at all."""


def ensure_key(candidate: object) -> int:
    """Return the validated key; anything but a bounded int is refused."""
    if isinstance(candidate, bool) or not isinstance(candidate, int):
        raise KeysError(f"not a key: {candidate!r} is not an integer")
    if candidate < MIN_KEY or candidate > MAX_KEY:
        raise KeysError(f"not a key: {candidate} leaves [{MIN_KEY}, {MAX_KEY}]")
    return candidate


def describe(key: int) -> str:
    """The display form of a key, the way the CLI prints it."""
    return str(key)

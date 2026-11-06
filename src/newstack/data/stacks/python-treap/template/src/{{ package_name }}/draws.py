"""Who stands above whom is settled by the seed, key by key.

The treap answers to two orders at the same time: keys fall down the
search tree the way a search tree orders them, and a draw decides who stands above whom
in the heap. A draw is a function of the seed and the key, never of
arrival order: same seed, same set of keys, identical shape, fed in any
order. The heap floor is the parent's promise to every child, and the
shape is arithmetic, never a mood.
"""

from __future__ import annotations

import hashlib

__all__ = ["DEFAULT_SEED", "MAX_PRIORITY", "DrawError", "Draws", "expected_depth"]

DEFAULT_SEED = 2026
MAX_PRIORITY = 1 << 40


class DrawError(ValueError):
    """The draws were asked for on terms no heap can keep."""


class Draws:
    """One seed: the heap number every key of this tree will ever wear."""

    def __init__(self, seed: int = DEFAULT_SEED) -> None:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise DrawError(f"{seed!r} is not a draw seed")
        self.seed = seed
        self.count = 0

    def shape_of(self, key: object) -> int:
        """The number this seed gives this key: small floats up, big sinks."""
        self.count += 1
        stamp = hashlib.blake2b(
            f"{self.seed}\0{key!r}".encode(), digest_size=8, person=b"treapdraw"
        )
        return int.from_bytes(stamp.digest(), "big") % MAX_PRIORITY


def expected_depth(size: int) -> int:
    """About how deep a treap of `size` keys stands: one bit per halving."""
    if not isinstance(size, int) or isinstance(size, bool) or size < 1:
        raise DrawError(f"{size!r} keys stand no tree")
    return size.bit_length() + 1

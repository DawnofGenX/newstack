"""A small deterministic generator, and a stable hash.

`hash()` is salted per interpreter, so a published signature would change
between runs and between machines. Everything here is built from blake2b
instead, which also means a stored signature can be compared after a restart.
"""

from __future__ import annotations

import hashlib

MASK = (1 << 64) - 1
GOLDEN = 0x9E3779B97F4A7C15


class RngError(ValueError):
    """A generator request that has no answer."""


class Rng:
    """SplitMix64: three lines, reproducible on every Python, no imports of `random`."""

    def __init__(self, seed: int) -> None:
        self.state = seed & MASK

    def next_u64(self) -> int:
        self.state = (self.state + GOLDEN) & MASK
        value = self.state
        value = (value ^ (value >> 30)) * 0xBF58476D1CE4E5B9 & MASK
        value = (value ^ (value >> 27)) * 0x94D049BB133111EB & MASK
        return value ^ (value >> 31)

    def below(self, bound: int) -> int:
        """A uniform integer in `0..bound-1`."""
        if bound < 1:
            raise RngError(f"below({bound}) has no values to return")
        return self.next_u64() % bound

    def random(self) -> float:
        """A uniform float in `[0, 1)` built from 53 bits, so it is exact in a float."""
        return (self.next_u64() >> 11) * (1.0 / (1 << 53))

    @staticmethod
    def stable_hash(item: str) -> int:
        """A 64-bit hash that is the same on every machine and every run."""
        digest = hashlib.blake2b(item.encode("utf-8"), digest_size=8, person=b"minhashl").digest()
        return int.from_bytes(digest, "big")

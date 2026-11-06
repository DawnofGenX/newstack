"""A tiny deterministic generator, so a published curve reproduces on every machine.

``random.Random`` is an implementation detail of CPython: its algorithm may change
between versions, and a demo whose numbers move is a demo nobody can check.
"""

from __future__ import annotations

import math

MASK = (1 << 64) - 1
GOLDEN = 0x9E3779B97F4A7C15


class RngError(ValueError):
    """A generator asked for something it cannot give."""


class Rng:
    """SplitMix64: one multiply-xor step per draw, and the same stream everywhere."""

    __slots__ = ("_state",)

    def __init__(self, seed: int = 0) -> None:
        self._state = seed & MASK

    def next_u64(self) -> int:
        self._state = (self._state + GOLDEN) & MASK
        z = self._state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def random(self) -> float:
        """A float in [0, 1): the top 53 bits, which is what a double can hold."""
        return (self.next_u64() >> 11) * (2.0**-53)

    def below(self, bound: int) -> int:
        if bound < 1:
            raise RngError(f"a bound needs at least one value, not {bound}")
        return self.next_u64() % bound

    def lognormal(self, median: float, sigma: float) -> float:
        """A positive latency: median * exp(normal * sigma), by the Box-Muller route."""
        u1 = 1.0 - self.random()
        u2 = self.random()
        normal = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return median * math.exp(normal * sigma)

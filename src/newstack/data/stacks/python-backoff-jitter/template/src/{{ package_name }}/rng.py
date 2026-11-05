"""A tiny deterministic generator, so a published failure curve can be reproduced.

``random.Random`` is stable in practice but its algorithm is an implementation
detail; SplitMix64 is 12 lines, has no state beyond one integer, and produces the
same sequence on every Python version, which is what makes the numbers in the
demo checkable by hand.
"""

from __future__ import annotations

MASK = (1 << 64) - 1
GOLDEN = 0x9E3779B97F4A7C15


class Rng:
    """SplitMix64."""

    __slots__ = ("state",)

    def __init__(self, seed: int = 0) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise TypeError(f"a seed is a whole number, not {type(seed).__name__}")
        self.state = seed & MASK

    def next_u64(self) -> int:
        self.state = (self.state + GOLDEN) & MASK
        value = self.state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK
        return value ^ (value >> 31)

    def random(self) -> float:
        """A float in [0, 1), built from the top 53 bits so no value is favoured."""
        return (self.next_u64() >> 11) * (2.0**-53)

    def uniform(self, low: float, high: float) -> float:
        if high < low:
            raise ValueError(f"cannot draw between {low} and {high}: the range is reversed")
        return low + (high - low) * self.random()

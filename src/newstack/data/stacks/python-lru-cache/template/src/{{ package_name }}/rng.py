"""SplitMix64: a generator small enough to read, so a published trace reproduces."""

from __future__ import annotations

MASK = (1 << 64) - 1
GOLDEN = 0x9E3779B97F4A7C15
TWO53 = float(1 << 53)


class RngError(ValueError):
    """A draw the generator cannot make."""


class Rng:
    """SplitMix64.

    `random.Random` is an implementation detail that has changed between releases;
    a stack that publishes hit ratios has to publish the stream those ratios came
    from, so the generator is twelve lines and never moves.
    """

    __slots__ = ("state",)

    def __init__(self, seed: int) -> None:
        self.state = seed & MASK

    def next_u64(self) -> int:
        self.state = (self.state + GOLDEN) & MASK
        value = self.state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK
        return value ^ (value >> 31)

    def below(self, bound: int) -> int:
        """A uniform integer in `0..bound-1`."""
        if bound < 1:
            raise RngError(f"a bound needs to be at least 1, not {bound}")
        limit = MASK - (MASK % bound)
        while True:
            draw = self.next_u64()
            if draw <= limit:
                return draw % bound

    def random(self) -> float:
        """A float in `[0, 1)` from the top 53 bits, which is exactly a double."""
        return (self.next_u64() >> 11) / TWO53

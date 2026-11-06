"""A generator that gives the same curve on every Python.

`random.Random` is an implementation detail: its algorithm may change between
versions, and a published false-positive rate that nobody can reproduce is not a
measurement. This is SplitMix64, written out, with the constants from the paper.
"""

from __future__ import annotations

import math

MASK = (1 << 64) - 1
GOLDEN = 0x9E3779B97F4A7C15
MIX_1 = 0xBF58476D1CE4E5B9
MIX_2 = 0x94D049BB133111EB
MIX_SHIFT = 30
MIX_SHIFT_2 = 27
MIX_SHIFT_3 = 31
UNIT = 2.0**-53


class Rng:
    """SplitMix64: a counter, three xor-shifts, and no hidden state elsewhere."""

    __slots__ = ("_state",)

    def __init__(self, seed: int) -> None:
        self._state = seed & MASK

    def next_u64(self) -> int:
        self._state = (self._state + GOLDEN) & MASK
        value = self._state
        value = ((value ^ (value >> MIX_SHIFT)) * MIX_1) & MASK
        value = ((value ^ (value >> MIX_SHIFT_2)) * MIX_2) & MASK
        return value ^ (value >> MIX_SHIFT_3)

    def random(self) -> float:
        """A float in [0, 1), from the top 53 bits so every value is representable."""
        return (self.next_u64() >> 11) * UNIT

    def below(self, limit: int) -> int:
        if limit < 1:
            raise ValueError(f"a limit must be at least 1, not {limit}")
        return self.next_u64() % limit


def bernoulli(rng: Rng, count: int, probability: float) -> int:
    """How many of `count` independent trials succeed.

    Drawn in geometric gaps rather than one coin per trial: the number of failures
    before the next success is `floor(log(U) / log(1 - p))`, so the cost follows
    the number of successes instead of the number of visitors. That is the same
    distribution with eleven million draws' worth of waiting removed.
    """
    if count < 0:
        raise ValueError(f"a trial count cannot be negative, not {count}")
    if not 0.0 <= probability <= 1.0:
        raise ValueError(f"a probability must be in 0..1, not {probability}")
    if probability == 0.0:
        return 0
    if probability == 1.0:
        return count
    log_failure = math.log1p(-probability)
    opening = 1.0 / (1 << 53)
    hits = 0
    position = 0
    while True:
        drawn = ((rng.next_u64() >> 11) + 1) * opening
        gap = math.floor(math.log(drawn) / log_failure)
        position += gap + 1
        if position > count:
            return hits
        hits += 1

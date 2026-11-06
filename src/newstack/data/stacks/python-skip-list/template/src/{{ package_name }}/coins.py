"""Coin flips that decide tower heights, and the shape they promise.

The shape of a skip list is the only part a caller can see of a random
process, so this module keeps the randomness in one addressable place:
one seeded generator, one flip rule, and a level cap derived from the
size of the map rather than from a mood. In this map a coin decides how
tall a tower may stand, and nothing else about it; same seed, same tower.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from math import log2

from .keys import SkipKeyValueError

__all__ = [
    "DEFAULT_SEED",
    "MAX_LEVEL",
    "CoinToss",
    "LevelPlan",
    "expected_level",
    "level_budget",
]

DEFAULT_SEED = 20260406
MAX_LEVEL = 16
_GROWTH = 2


class CoinTossError(SkipKeyValueError):
    """A flip was asked for with inputs that cannot be flipped."""


def expected_level(count: int) -> int:
    """The level a p=1/2 tower reaches after `count` towers.

    Levels are geometric, so the tallest tower is around log2(count);
    callers compare against this instead of a hand-written constant.
    """
    if count <= 1:
        return 1
    return int(log2(count)) + 1


def level_budget(count: int, cap: int = MAX_LEVEL) -> int:
    """How tall a level index may be when `count` keys are stored."""
    return min(cap, max(1, expected_level(count) + 1))


@dataclass(frozen=True)
class LevelPlan:
    """What one run of flips produced: the levels and the flip count."""

    levels: tuple[int, ...] = field(default=())
    flips: int = 0
    heads: int = 0

    @property
    def tallest(self) -> int:
        return max(self.levels, default=0)

    @property
    def shortest(self) -> int:
        return min(self.levels, default=0)

    @property
    def mean_level(self) -> float:
        if not self.levels:
            return 0.0
        return sum(self.levels) / len(self.levels)

    def summary(self) -> str:
        return (
            f"towers {len(self.levels)} tallest {self.tallest} "
            f"mean {self.mean_level:.2f} flips {self.flips} heads {self.heads}"
        )


class CoinToss:
    """Flip a fair coin until it lands tails; count the heads.

    A tower stands one story per head, so heights come out geometric and
    the map stays balanced without rotations. The generator is owned, not
    borrowed, so a caller's seed is not disturbed by anything else.
    """

    def __init__(self, seed: int = DEFAULT_SEED, cap: int = MAX_LEVEL) -> None:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise CoinTossError(f"{seed!r} is not a seed")
        if cap < 1:
            raise CoinTossError(f"a cap of {cap} allows no tower")
        self.seed = seed
        self.cap = cap
        self._rng = random.Random(seed)
        self.flips = 0
        self.heads = 0

    def level(self, cap: int | None = None) -> int:
        """Heights are counted from 0; a cap of n allows n - 1 stories."""
        limit = self.cap if cap is None else cap
        if limit < 1:
            raise CoinTossError(f"a cap of {limit} allows no tower")
        heads = 0
        while heads < limit - 1 and self._rng.random() < 0.5:
            heads += 1
            self.flips += 1
            self.heads += 1
        self.flips += 1
        return heads

    def plan(self, count: int) -> LevelPlan:
        """`count` flips in a row, kept as a plan, never recomputed."""
        if count < 0:
            raise CoinTossError(f"{count} towers cannot be flipped for")
        before = self.flips
        levels = tuple(self.level() for _ in range(count))
        return LevelPlan(levels, self.flips - before, self.heads)

    def reroll(self) -> CoinToss:
        """A second toss on the same seed, for callers who want a twin."""
        twin = CoinToss(self.seed, self.cap)
        twin.plan(1)
        twin.flips = 0
        twin.heads = 0
        return twin

    def fork(self, salt: int) -> CoinToss:
        """A different stream, still derived from the same seed."""
        return CoinToss(self.seed + salt, self.cap)

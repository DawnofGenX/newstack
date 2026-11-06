"""MinHash: a fixed-size signature whose agreement estimates Jaccard.

For one random permutation of the shingle universe, the probability that the
smallest hashed shingle of two sets is the same is exactly their Jaccard
similarity. So the fraction of positions where two signatures agree is an
unbiased estimate, and its error is a binomial standard deviation of
`1/sqrt(width)` -- a number that can be predicted before any data arrives.
"""

from __future__ import annotations

import math

from .rng import Rng
from .shingles import ShingleError, shingles

# A Mersenne prime, so `a*x + b mod P` is a family of permutations that is cheap
# to evaluate and has no floating-point step.
P = (1 << 61) - 1
DEFAULT_WIDTH = 128
DEFAULT_SHINGLE = 5


class MinHashError(ValueError):
    """A signature request that cannot be answered honestly."""


def permutations(width: int, seed: int = 7) -> tuple[tuple[int, int], ...]:
    """`width` distinct affine permutations of the shingle universe."""
    if width < 1:
        raise MinHashError(f"a signature needs at least one position, not {width}")
    rng = Rng(seed)
    seen: set[tuple[int, int]] = set()
    family: list[tuple[int, int]] = []
    while len(family) < width:
        a = rng.below(P - 1) + 1
        b = rng.below(P)
        if (a, b) in seen:
            continue
        seen.add((a, b))
        family.append((a, b))
    return tuple(family)


class MinHash:
    """A signature scheme: width positions, one shingle size, one seed."""

    def __init__(
        self, width: int = DEFAULT_WIDTH, *, shingle_size: int = DEFAULT_SHINGLE, seed: int = 7
    ):
        if width < 1:
            raise MinHashError(f"a signature needs at least one position, not {width}")
        if shingle_size < 1:
            raise ShingleError(f"a shingle needs at least one word, not {shingle_size}")
        self.width = width
        self.shingle_size = shingle_size
        self.seed = seed
        self.family = permutations(width, seed)
        self.documents = 0

    @property
    def error(self) -> float:
        """One standard deviation of the estimate, from the width alone."""
        return 1.0 / math.sqrt(self.width)

    def signature(self, text: str) -> tuple[int, ...]:
        return self.signature_of(shingles(text, self.shingle_size))

    def signature_of(self, items: frozenset[str]) -> tuple[int, ...]:
        if not items:
            raise ShingleError("a document with no shingles has no signature")
        hashed = [self._hash(item) for item in items]
        self.documents += 1
        return tuple(min((a * value + b) % P for value in hashed) for a, b in self.family)

    def _hash(self, item: str) -> int:
        return Rng.stable_hash(item)

    def estimate(self, left: tuple[int, ...], right: tuple[int, ...]) -> float:
        """The share of positions where two signatures agree."""
        if len(left) != len(right):
            raise MinHashError(
                f"signatures of width {len(left)} and {len(right)} cannot be compared: "
                "they were not built from the same permutations"
            )
        return sum(1 for a, b in zip(left, right, strict=True) if a == b) / len(left)

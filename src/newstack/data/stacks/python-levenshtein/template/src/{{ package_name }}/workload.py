"""Seeded pair storms, re-checked after every draw.

The workload is the falsifier with a memory: it draws words, asks the
row walk for distances, and after every single draw re-checks
symmetry, the triangle inequality on triples, and the nearest listing
against the scan's ordering. A break counter the storm cannot push
past zero is the only report here worth printing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .corpus import DEFAULT_SEED, synthetic
from .distance import distance, rank_pairs
from .words import ensure_word

DEFAULT_STEPS = 160


class WorkloadError(ValueError):
    """The storm was asked for steps it cannot script."""

    __slots__ = ()


@dataclass(frozen=True)
class Replay:
    """What the storm spent and whether any answer it took was wrong."""

    steps: int
    checks: int
    breaks: int
    words: int
    ties: int

    @property
    def clean(self) -> bool:
        return self.breaks == 0


def run_storm(
    steps: int = DEFAULT_STEPS, seed: int = DEFAULT_SEED, pool: int = 80
) -> Replay:
    """Distances, triples, and nearest listings, re-checked per draw."""
    if steps <= 0 or pool <= 0:
        raise WorkloadError("a storm needs positive steps and pool")
    rng = random.Random(seed)
    corpus = synthetic(pool, seed=seed)
    breaks = 0
    checks = 0
    ties = 0
    for _ in range(steps):
        left = rng.choice(corpus)
        right = rng.choice(corpus)
        checks += 1
        if distance(left, right) != distance(right, left):
            breaks += 1
        far = rng.choice(corpus)
        checks += 1
        if distance(left, right) > distance(left, far) + distance(far, right):
            breaks += 1
        listing = rank_pairs(left, corpus)
        checks += 1
        if listing != sorted(listing, key=lambda pair: (pair[0], pair[1])):
            breaks += 1
        best = distance(left, listing[0][1])
        checks += 1
        if any(best > distance(left, word) for word in corpus):
            breaks += 1
        head, second = listing[0], listing[1]
        if head[0] == second[0] and head[1] > second[1]:
            breaks += 1
        if head[0] == second[0]:
            ties += 1
    return Replay(
        steps=steps, checks=checks, breaks=breaks, words=len(corpus), ties=ties
    )


def shuffle_matches(corpus: list[str], seed: int = DEFAULT_SEED) -> bool:
    """Two orderings of one corpus answer identically, forever after."""
    rng = random.Random(seed)
    shuffled = list(corpus)
    rng.shuffle(shuffled)
    probes = [rng.choice(corpus) for _ in range(40)]
    return all(rank_pairs(probe, corpus) == rank_pairs(probe, shuffled)
               for probe in probes)


def live_distances(pairs: list[tuple[str, str]]) -> list[int]:
    """The walk over shipped pairs; each side passes the word gate first."""
    return [distance(ensure_word(a), ensure_word(b)) for a, b in pairs]

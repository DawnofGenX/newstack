"""Seeded storms of inserts, deletes, and queries, checked after every op.

The workload is the falsifier with a memory: it drives the trie through
a scripted sequence, and after every single op it re-reads membership
and the prefix listing against a plain set and a plain sorted scan. A
break counter the storm cannot push past zero is the only report here
worth printing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .corpus import DEFAULT_SEED, synthetic
from .scan import scan_has, scan_prefix
from .trie import PrefixTrie

DEFAULT_STEPS = 160


@dataclass(frozen=True)
class Replay:
    """What the storm spent and whether anything it held was wrong."""

    steps: int
    checks: int
    breaks: int
    words: int
    ordered: bool

    @property
    def clean(self) -> bool:
        return self.breaks == 0 and self.ordered


class WorkloadError(ValueError):
    """The storm was asked for steps it cannot script."""

    __slots__ = ()


def run_storm(
    steps: int = DEFAULT_STEPS, seed: int = DEFAULT_SEED, pool: int = 80
) -> Replay:
    """Insert, delete, ask; re-check the set and the listing after every op."""
    if steps <= 0 or pool <= 0:
        raise WorkloadError("a storm needs positive steps and pool")
    rng = random.Random(seed)
    corpus = synthetic(pool, seed=seed)
    trie = PrefixTrie()
    held: set[str] = set()
    breaks = 0
    checks = 0
    for _ in range(steps):
        move = rng.random()
        if move < 0.55:
            word = rng.choice(corpus)
            trie.insert(word)
            held.add(word)
        elif move < 0.75 and held:
            word = rng.choice(sorted(held))
            trie.delete(word)
            held.discard(word)
        elif move < 0.9 and held:
            word = rng.choice(sorted(held))
            checks += 1
            if trie.has(word) is not scan_has(sorted(held), word):
                breaks += 1
        else:
            stem = rng.choice(corpus)[: rng.randint(0, 3)]
            checks += 1
            if trie.prefix(stem) != scan_prefix(sorted(held), stem):
                breaks += 1
        checks += 1
        if trie.count() != len(held):
            breaks += 1
        if not trie.invariant():
            breaks += 1
    listing = trie.walk()
    return Replay(
        steps=steps,
        checks=checks,
        breaks=breaks,
        words=trie.count(),
        ordered=listing == sorted(held),
    )


def rebuild_matches(corpus: list[str], seed: int = DEFAULT_SEED) -> bool:
    """Two tries fed the same corpus answer identically, forever after."""
    first = PrefixTrie(corpus)
    second = PrefixTrie(reversed(sorted(corpus)))
    rng = random.Random(seed)
    probes = [rng.choice(corpus) for _ in range(40)]
    for probe in probes:
        stem = probe[:2]
        if first.has(probe) != second.has(probe):
            return False
        if first.prefix(stem) != second.prefix(stem):
            return False
    return first.walk() == second.walk() == sorted(set(corpus))

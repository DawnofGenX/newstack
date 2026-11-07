"""Seeded streams of adds, re-audited after every single update.

The workload is the falsifier with a memory: it drives a sketch
through scripted streams and, after every add, checks the promise
every tracked count still answers at least its ledger truth. The
break counter is the only report here worth printing; with the
shipped configuration the drift counter stays at zero too, because
rows are bijections on a universe the width can seat alone.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .corpus import DEFAULT_SEED, synthetic
from .hashes import DEPTH, MULTIPLIERS, WIDTH
from .sketch import CountMinSketch

DEFAULT_STEPS = 140


class WorkloadError(ValueError):
    """The stream was asked for steps it cannot script."""

    __slots__ = ()


@dataclass(frozen=True)
class Replay:
    """What the stream spent and whether any promise it watched broke."""

    steps: int
    checks: int
    breaks: int
    exact: int
    drift: int
    seated: bool

    @property
    def clean(self) -> bool:
        return self.breaks == 0 and self.seated


def run_stream(
    steps: int = DEFAULT_STEPS,
    seed: int = DEFAULT_SEED,
    width: int = WIDTH,
    depth: int = DEPTH,
    multipliers: tuple[int, ...] = MULTIPLIERS,
) -> Replay:
    """Add scripted events; re-audit every tracked count after every add."""
    if steps <= 0:
        raise WorkloadError(f"no stream from {steps} steps")
    rng = random.Random(seed)
    sketch = CountMinSketch(width, depth, multipliers)
    checks = 0
    breaks = 0
    for key, n in synthetic(steps, seed=rng.randrange(1, 2**31)):
        sketch.add(key, n)
        checks += len(sketch)
        for tracked in sketch:
            if sketch.count(tracked) < sketch.true_count(tracked):
                breaks += 1
    exact = sum(
        1 for tracked in sketch if sketch.count(tracked) == sketch.true_count(tracked)
    )
    tracked_total = len(sketch)
    return Replay(
        steps=steps,
        checks=checks,
        breaks=breaks,
        exact=exact,
        drift=tracked_total - exact,
        seated=not sketch.audit(),
    )


def stream_matches(shape: str = "shipped") -> bool:
    """Whether the named shape answers the shipped corpora exactly."""
    multipliers = MULTIPLIERS if shape == "shipped" else (3, 5, 7, 11, 13)
    width = WIDTH if shape == "shipped" else 64
    for seed in (3, 91):
        replay = run_stream(steps=60, seed=seed, width=width, multipliers=multipliers)
        if not replay.clean:
            return False
    return True

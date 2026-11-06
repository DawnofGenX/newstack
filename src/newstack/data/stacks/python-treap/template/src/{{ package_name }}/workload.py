"""A seeded mixed workload: every op re-checks both orders, live.

Inserts, deletes, probes, and ranks arrive in one seeded stream, and
after every single one the tree is asked the same two questions: does
the search order still hold, and does the heap floor still hold. The
replay is what makes the treap falsifiable — a merge that forgets its
swap or a split that leaks a key shows up here as a counted break,
never as a silent green.
"""

from __future__ import annotations

import bisect
import random
from dataclasses import dataclass

from .draws import DEFAULT_SEED
from .treap import Treap

__all__ = ["Replay", "WorkloadError", "run_workload"]


class WorkloadError(ValueError):
    """The workload was asked on terms no replay can honour."""


@dataclass(frozen=True)
class Replay:
    """One mixed workload, answered: checks run, order breaks found."""

    seed: int
    steps: int
    checks: int
    breaks: int
    size: int
    log: tuple[str, ...]

    def line(self) -> str:
        return (
            f"seed {self.seed} steps {self.steps} checks {self.checks} "
            f"breaks {self.breaks} size {self.size}"
        )


def run_workload(seed: int = DEFAULT_SEED, size: int = 48, steps: int = 160) -> Replay:
    """Insert, delete, and probe in one seeded storm, checking after each."""
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise WorkloadError(f"{seed!r} is not a workload seed")
    if not 1 <= size <= 5_000 or not 1 <= steps <= 50_000:
        raise WorkloadError("the workload is outside its honest bounds")
    rng = random.Random(seed)
    tree = Treap(seed)
    ordered: list[int] = []
    log: list[str] = []
    checks = breaks = 0
    for step in range(steps):
        key = rng.randrange(-size * 6, size * 6)
        kind = rng.randrange(5)
        if kind < 2:
            tree.insert(key, step)
            if key not in ordered:
                ordered.append(key)
                ordered.sort()
            log.append(f"step {step:>4} insert {key:>6}")
        elif kind == 2:
            tree.delete(key)
            ordered = [item for item in ordered if item != key]
            log.append(f"step {step:>4} delete {key:>6}")
        elif kind == 3:
            tree.contains(key)
            log.append(f"step {step:>4} probe  {key:>6}")
        else:
            want = bisect.bisect_left(ordered, key)
            got = tree.rank(key)
            checks += 1
            breaks += int(got != want)
            log.append(f"step {step:>4} rank   {key:>6} -> {got}")
        bst, heap = tree.stats()["broken"]  # type: ignore[assignment]
        checks += 1
        breaks += int(bst or heap)
        if tree.pairs() != [(item, tree.get(item)) for item in ordered]:
            checks += 1
            breaks += 1
        else:
            checks += 1
    return Replay(seed, steps, checks, breaks, len(tree), tuple(log))

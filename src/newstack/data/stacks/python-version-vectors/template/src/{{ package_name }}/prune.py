"""Compaction: dropping the counters every replica already agrees on.

A vector that keeps every node it has ever heard from grows without bound, so a real
system truncates the entries that sit at a floor every replica has passed. That is
sound for vectors that dominate the floor, and it is *not* sound for vectors below it -
and the difference is measurable, which is the point of this module.
"""

from __future__ import annotations

from dataclasses import dataclass

from .vector import Relation, VersionVector


class PruneError(ValueError):
    """A floor or a compaction that cannot be performed as asked."""


def floor_of(vectors: list[VersionVector]) -> VersionVector:
    """The pointwise minimum: what every one of these vectors has already seen."""
    if not vectors:
        raise PruneError("a floor needs at least one vector to take the minimum of")
    nodes: set[str] = set()
    for vector in vectors:
        nodes.update(vector.nodes())
    counts = {node: min(vector.get(node) for vector in vectors) for node in nodes}
    return VersionVector(counts)


def compact(vector: VersionVector, floor: VersionVector) -> VersionVector:
    """Drop every counter that sits at the floor, keeping the rest as they are.

    Nothing is added and no counter is lowered: an entry equal to the floor is the
    entry every replica has, so it carries no information about this vector's position
    relative to another vector that also dominates the floor.
    """
    counts = {node: count for node, count in vector.counts().items() if count > floor.get(node)}
    return VersionVector(counts)


def dominates_floor(vector: VersionVector, floor: VersionVector) -> bool:
    return vector.dominates(floor)


@dataclass(frozen=True)
class Measurement:
    """How many comparisons compaction changed, split by whether the floor covers them."""

    vectors: int
    pairs: int
    above: int
    below: int
    changed_above: int
    changed_below: int
    examples_below: tuple[str, ...] = ()

    def held(self) -> bool:
        """The claim: exact above the floor, and lossy below it when anything is below.

        A measurement with no pairs below the floor only establishes the safe half,
        which is why the second half is checked only when it has something to check.
        """
        return self.changed_above == 0 and (self.below == 0 or self.changed_below > 0)

    def lines(self) -> list[str]:
        return [
            f"vectors      {self.vectors}, pairs {self.pairs}",
            f"above floor  {self.above} pair(s), {self.changed_above} verdict(s) changed",
            f"below floor  {self.below} pair(s), {self.changed_below} verdict(s) changed",
            f"sound above  {'yes' if self.changed_above == 0 else 'NO'}",
        ]


def measure(vectors: list[VersionVector], floor: VersionVector) -> Measurement:
    """Compare every pair before and after compaction, and count what changed.

    Above the floor the verdict must be identical; below it, a vector that never
    reached the floor has counters the compaction erased, and two different states can
    collapse into the same compacted vector - which reads as EQUAL, or as BEFORE, when
    the uncompacted pair said CONCURRENT.
    """
    if not vectors:
        raise PruneError("a measurement needs at least one vector")
    squeezed = [compact(vector, floor) for vector in vectors]
    above = below = changed_above = changed_below = 0
    examples: list[str] = []
    for left in range(len(vectors)):
        for right in range(left + 1, len(vectors)):
            before = vectors[left].compare(vectors[right])
            after = squeezed[left].compare(squeezed[right])
            covered = dominates_floor(vectors[left], floor) and dominates_floor(
                vectors[right], floor
            )
            if covered:
                above += 1
                if before is not after:
                    changed_above += 1
            else:
                below += 1
                if before is not after:
                    changed_below += 1
                    line = (
                        f"{vectors[left].text() or 'empty'} vs {vectors[right].text() or 'empty'}: "
                        f"{before.value} became {after.value}"
                    )
                    if line not in examples and len(examples) < 3:
                        examples.append(line)
    return Measurement(
        vectors=len(vectors),
        pairs=len(vectors) * (len(vectors) - 1) // 2,
        above=above,
        below=below,
        changed_above=changed_above,
        changed_below=changed_below,
        examples_below=tuple(examples),
    )


def compacted_relation(
    left: VersionVector, right: VersionVector, floor: VersionVector
) -> tuple[Relation, Relation]:
    """Both verdicts at once, so a caller can print the difference instead of hiding it."""
    return left.compare(right), compact(left, floor).compare(compact(right, floor))

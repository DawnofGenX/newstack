"""Clustering: candidates first, then an estimate, then a decision.

Banding is a filter, not an answer. Every candidate pair is checked against the
signature estimate before two documents are called the same, because `1-1/sqrt(width)`
of a banding's certainty is not a cluster boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

from .lsh import Bands, LshError


class DedupeError(ValueError):
    """A clustering request that cannot be answered."""


class _Union:
    def __init__(self, names: list[str]) -> None:
        self.parent = {name: name for name in names}

    def find(self, name: str) -> str:
        while self.parent[name] != name:
            self.parent[name] = self.parent[self.parent[name]]
            name = self.parent[name]
        return name

    def join(self, left: str, right: str) -> bool:
        first, second = self.find(left), self.find(right)
        if first == second:
            return False
        self.parent[max(first, second)] = min(first, second)
        return True


@dataclass(frozen=True)
class Groups:
    """Clusters are sorted, so two runs print the same thing."""

    clusters: tuple[tuple[str, ...], ...]
    joined: int
    rejected: int
    candidates: int

    @property
    def count(self) -> int:
        return len(self.clusters)

    @property
    def duplicates(self) -> int:
        return sum(len(cluster) - 1 for cluster in self.clusters)

    def lines(self) -> list[str]:
        rows = [
            f"documents    {sum(len(cluster) for cluster in self.clusters)}",
            f"candidates   {self.candidates}",
            f"joined       {self.joined} pair(s), {self.rejected} refused by the estimate",
            f"clusters     {self.count} ({self.duplicates} duplicate(s) folded in)",
        ]
        for number, cluster in enumerate(self.clusters, start=1):
            if len(cluster) > 1:
                rows.append(f"  {number:>2}. {', '.join(cluster)}")
        return rows


def cluster(
    signatures: dict[str, tuple[int, ...]],
    bands: Bands,
    *,
    threshold: float = 0.8,
    estimate: float | None = None,
) -> Groups:
    """Group names whose signature agreement reaches `threshold`."""
    if not signatures:
        raise DedupeError("there is nothing to cluster")
    if not 0.0 <= threshold <= 1.0:
        raise DedupeError(f"a threshold is a similarity in 0..1, not {threshold}")
    width = bands.width
    for name, signature in signatures.items():
        if len(signature) < width:
            raise LshError(f"{name} has {len(signature)} position(s) but the banding needs {width}")
    pairs = bands.candidates(signatures)
    union = _Union(sorted(signatures))
    joined = rejected = 0
    for left, right in pairs:
        agreement = (
            sum(
                1
                for a, b in zip(signatures[left][:width], signatures[right][:width], strict=True)
                if a == b
            )
            / width
        )
        if agreement < threshold:
            rejected += 1
        elif union.join(left, right):
            joined += 1
    members: dict[str, list[str]] = {}
    for name in sorted(signatures):
        members.setdefault(union.find(name), []).append(name)
    clusters = tuple(sorted(tuple(sorted(group)) for group in members.values()))
    return Groups(clusters=clusters, joined=joined, rejected=rejected, candidates=len(pairs))

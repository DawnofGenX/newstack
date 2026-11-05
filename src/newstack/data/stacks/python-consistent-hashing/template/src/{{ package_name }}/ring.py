"""A hash ring with virtual nodes, weights and a tie-break you can predict."""

from __future__ import annotations

from bisect import bisect_left
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from .hashing import WIDTH, hash64, virtual_node_key

DEFAULT_VNODES = 160


class RingError(ValueError):
    """A ring that cannot answer honestly."""


@dataclass(frozen=True, order=True)
class Point:
    """One position on the ring, owned by ``node``."""

    position: int
    node: str

    def text(self) -> str:
        return f"{self.position:020d} {self.node}"


class Ring:
    """Consistent hashing: a key belongs to the first point clockwise from its hash.

    ``vnodes`` points per unit of weight is what makes the share of keys per node close to
    its share of weight: one point per node leaves the split at the mercy of where those
    points happened to land.
    """

    def __init__(self, *, vnodes: int = DEFAULT_VNODES) -> None:
        if vnodes < 1:
            raise RingError(f"vnodes must be at least 1, got {vnodes}")
        self.vnodes = vnodes
        self._points: list[Point] = []
        self._weights: dict[str, int] = {}

    # -- membership -------------------------------------------------------------------
    def add(self, node: str, weight: int = 1) -> None:
        if not node:
            raise RingError("a node needs a name")
        if node in self._weights:
            raise RingError(f"node {node!r} is already on the ring")
        if weight < 1:
            raise RingError(f"weight must be at least 1, got {weight}")
        self._weights[node] = weight
        self._points.extend(self._points_for(node, weight))
        self._points.sort()

    def remove(self, node: str) -> None:
        if node not in self._weights:
            raise RingError(f"node {node!r} is not on the ring")
        del self._weights[node]
        self._points = [point for point in self._points if point.node != node]

    def _points_for(self, node: str, weight: int) -> list[Point]:
        return [
            Point(hash64(virtual_node_key(node, index)), node)
            for index in range(self.vnodes * weight)
        ]

    # -- lookup -----------------------------------------------------------------------
    @property
    def nodes(self) -> list[str]:
        return sorted(self._weights)

    @property
    def points(self) -> list[Point]:
        return list(self._points)

    def weight_of(self, node: str) -> int:
        return self._weights[node]

    def get(self, key: str) -> str:
        if not self._points:
            raise RingError("the ring is empty: every key would be lost, not placed")
        position = hash64(key)
        index = bisect_left(self._points, Point(position, ""))
        if index == len(self._points):
            # Past the last point, the ring wraps to the first one. Forgetting this is how
            # ~1/points of the keys end up unsupported.
            index = 0
        return self._points[index].node

    def owner(self, key: str) -> Point:
        if not self._points:
            raise RingError("the ring is empty")
        position = hash64(key)
        index = bisect_left(self._points, Point(position, ""))
        if index == len(self._points):
            index = 0
        return self._points[index]

    def mapping(self, keys: Iterable[str]) -> dict[str, str]:
        return {key: self.get(key) for key in keys}

    # -- shape ------------------------------------------------------------------------
    def loads(self, keys: Iterable[str]) -> dict[str, int]:
        counted = Counter(self.get(key) for key in keys)
        return {node: counted.get(node, 0) for node in self.nodes}

    def shares(self, keys: Iterable[str]) -> dict[str, float]:
        counted = Counter(self.get(key) for key in keys)
        total = sum(counted.values())
        if total == 0:
            return {node: 0.0 for node in self.nodes}
        return {node: counted.get(node, 0) / total for node in self.nodes}

    def arc_loads(self) -> dict[str, int]:
        """How much of the ring each node owns, from the point spacing alone.

        No keys are sampled here: this is the ring's own shape. The share of *keys* a node
        gets converges on its arc share, but with a fixed key set the sampling noise does not
        shrink when you add more points, which is why a measured imbalance can stop improving.
        """
        if not self._points:
            raise RingError("the ring is empty")
        arcs: dict[str, int] = {node: 0 for node in self._weights}
        for index, point in enumerate(self._points):
            following = self._points[(index + 1) % len(self._points)]
            end = following.position + (WIDTH if index == len(self._points) - 1 else 0)
            arcs[point.node] += end - point.position
        return arcs

    def arc_imbalance(self) -> float:
        arcs = self.arc_loads()
        smallest = min(arcs.values())
        if smallest <= 0:
            return float("inf")
        return max(arcs.values()) / smallest

    def imbalance(self, keys: Iterable[str]) -> float:
        """Largest share divided by the smallest: 1.0 is a perfect split."""
        shares = [share for share in self.shares(keys).values()]
        if not shares or min(shares) <= 0:
            return float("inf")
        return max(shares) / min(shares)

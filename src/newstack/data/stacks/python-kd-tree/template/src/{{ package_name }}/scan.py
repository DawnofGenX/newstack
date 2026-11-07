"""The scan is the oracle: one comparison per point, no structure at all.

Every answer the tree gives must equal what this module answers on the
same corpus. If a structure cannot beat a scan's honesty with its own
speed, the structure is a confession, and these functions are the
sentence it is compared against.
"""

from __future__ import annotations

from .points import ensure_point, ensure_rect
from .tree import Point, distance, inside


def scan_has(points: list[Point], point: object) -> bool:
    """Membership by walking the corpus once."""
    pair = ensure_point(point)
    return any(held == pair for held in points)


def scan_range(points: list[Point], rect: object) -> list[Point]:
    """The sorted listing of every corpus point inside the rectangle."""
    box = ensure_rect(rect)
    return sorted(point for point in points if inside(point, box))


def scan_nearest(points: list[Point], query: object) -> Point | None:
    """The argmin of squared distance; ties go to the smallest point.

    The brute-force answer walks the whole corpus, so the tie rule the
    tree must match is written here: the lexicographically smallest
    point among the closest.
    """
    probe = ensure_point(query)
    best: tuple[tuple[int, int, int], Point] | None = None
    for point in points:
        key = (distance(point, probe), point[0], point[1])
        if best is None or key < best[0]:
            best = (key, point)
    return None if best is None else best[1]

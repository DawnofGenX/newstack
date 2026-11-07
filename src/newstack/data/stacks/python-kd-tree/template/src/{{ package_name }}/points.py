"""The gate: integer pairs in, points out, bounded inside the plane.

A point is two bounded integers. The gate refuses half-points, floats,
floats pretending to be ints, and coordinates past the edge, so points
reach the splits whole or not at all.
"""

from __future__ import annotations

MAX_COORD = 10**9
AXES = ("x", "y")


class PointError(ValueError):
    """A candidate is no point at all."""

    __slots__ = ()


def _axis(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PointError(f"not a point: {name} {value!r} is not an integer")
    if abs(value) > MAX_COORD:
        raise PointError(f"not a point: {name} {value} is past the plane edge")
    return value


def ensure_point(candidate: object) -> tuple[int, int]:
    """Return the validated pair; refuse everything else by name."""
    if isinstance(candidate, tuple) and len(candidate) == 2:
        x, y = candidate
        return _axis(x, "x"), _axis(y, "y")
    raise PointError(f"not a point: {candidate!r} is not an integer pair")


def ensure_rect(candidate: object) -> tuple[int, int, int, int]:
    """Return the validated rectangle; degenerate edges are legal."""
    if isinstance(candidate, tuple) and len(candidate) == 4:
        x_min, y_min, x_max, y_max = (
            _axis(edge, "edge") for edge in candidate
        )
        if x_min > x_max or y_min > y_max:
            raise PointError(
                f"not a rectangle: {candidate!r} has min past max"
            )
        return x_min, y_min, x_max, y_max
    raise PointError(f"not a rectangle: {candidate!r} is not four integers")


def describe(point: tuple[int, int]) -> str:
    """The display form of a point, printed the way the CLI prints it."""
    return f"({point[0]}, {point[1]})"

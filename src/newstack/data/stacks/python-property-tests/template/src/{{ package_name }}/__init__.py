"""Half-open interval arithmetic, checked by properties instead of examples."""

from __future__ import annotations

from .intervals import (
    Interval,
    coverage,
    expand,
    intersect,
    normalize,
    points_to_intervals,
    subtract,
)

__version__ = "1.0.0"

__all__ = [
    "Interval",
    "coverage",
    "expand",
    "intersect",
    "normalize",
    "points_to_intervals",
    "subtract",
]

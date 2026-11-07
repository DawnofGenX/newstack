"""A 2-d kd-tree over integer point pairs, and the scan that checks it.

A split divides, never the answer: the splits carry decisions, the
nodes carry points, and the selftest refuses to pass when a nearest
answer stops equaling the brute-force argmin or a rectangle answer
stops equaling the filter.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_points,
    parse_point,
    synthetic,
    write_points,
)
from .points import MAX_COORD, PointError, describe, ensure_point, ensure_rect
from .scan import scan_has, scan_nearest, scan_range
from .selftest import Report, run
from .tree import KDTree, TreeError, distance, inside
from .workload import Replay, WorkloadError, rebuild_matches, run_storm

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_COORD",
    "CorpusError",
    "KDTree",
    "PointError",
    "Replay",
    "Report",
    "Snapshot",
    "TreeError",
    "WorkloadError",
    "__version__",
    "describe",
    "distance",
    "ensure_point",
    "ensure_rect",
    "inside",
    "load_points",
    "parse_point",
    "rebuild_matches",
    "run",
    "run_storm",
    "scan_has",
    "scan_nearest",
    "scan_range",
    "synthetic",
    "write_points",
]

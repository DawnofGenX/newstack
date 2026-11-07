"""Integer values in, prefix sums out, and the bits that carry them.

The lowest set bit is the step: an add climbs the cells one jump at a
time, a prefix walks back down the same ladder, and no walk ever visits
more cells than the bit-length of the size. Every prefix equals the
running list-sum reference on seeded add/sum workloads, and the selftest
refuses to pass when one stops holding.
"""

from __future__ import annotations

from .fenwick import (
    Fenwick,
    FenwickError,
    Walk,
    build_cells,
    step_of,
)
from .streams import (
    DEFAULT_SEED,
    Snapshot,
    StreamError,
    load_values,
    rising,
    synthetic,
    write_values,
)
from .values import ValueRejection, describe, ensure_value, step_size
from .workload import Replay, WorkloadError, run_storm, run_walks, run_workload

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "Fenwick",
    "FenwickError",
    "Replay",
    "Snapshot",
    "StreamError",
    "ValueRejection",
    "Walk",
    "WorkloadError",
    "__version__",
    "build_cells",
    "describe",
    "ensure_value",
    "load_values",
    "rising",
    "run_storm",
    "run_walks",
    "run_workload",
    "step_of",
    "step_size",
    "synthetic",
    "write_values",
]

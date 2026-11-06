"""Log-structured merge tables, numbered level files, and workloads.

The table answers newest-level-first, the level files freeze one flush,
and the workloads are the stories that prove every answer equals the
plain-dict answer.
"""

from __future__ import annotations

from .levels import LevelError, MergeReport, read_table, write_table
from .ops import OpsError, load_ops, replay_dict, workload
from .table import LSMTable, TableError

__version__ = "0.1.0"

__all__ = [
    "LSMTable",
    "LevelError",
    "MergeReport",
    "OpsError",
    "TableError",
    "__version__",
    "load_ops",
    "read_table",
    "replay_dict",
    "workload",
    "write_table",
]

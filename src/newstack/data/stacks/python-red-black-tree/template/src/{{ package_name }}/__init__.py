"""A red-black tree over bounded integer keys, checked after every op.

The in-order walk is the sorted list of the keys held, and the checker
names nothing about the shape: root black, no red node fathers a red
child, equal black height on every path. ``selftest`` refuses to pass
when one of these promises stops holding on a seeded storm.
"""

from __future__ import annotations

from .check import (
    BLACK,
    RED,
    black_height,
    edge_heights,
    holds,
    is_red,
    problems,
)
from .check import (
    BLACK as BLACK_NODE,
)
from .corpus import (
    CorpusError,
    Snapshot,
    load_keys,
    parse_key,
    synthetic,
    write_keys,
)
from .demo import Story
from .demo import stories as demo_stories
from .keys import MAX_KEY, KeyError, describe_key, ensure_key
from .node import Node
from .selftest import Report
from .selftest import run as selftest_run
from .tree import RBTree, TreeError
from .workload import (
    Replay,
    WorkloadError,
    rebuild_matches,
    run_storm,
)

__version__ = "0.1.0"

__all__ = [
    "BLACK",
    "BLACK_NODE",
    "MAX_KEY",
    "RED",
    "CorpusError",
    "KeyError",
    "Node",
    "RBTree",
    "Replay",
    "Report",
    "Snapshot",
    "Story",
    "TreeError",
    "WorkloadError",
    "__version__",
    "black_height",
    "demo_stories",
    "describe_key",
    "edge_heights",
    "ensure_key",
    "holds",
    "is_red",
    "load_keys",
    "parse_key",
    "problems",
    "rebuild_matches",
    "run_storm",
    "selftest_run",
    "synthetic",
    "write_keys",
]

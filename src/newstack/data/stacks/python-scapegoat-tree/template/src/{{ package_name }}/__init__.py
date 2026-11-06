"""A search tree whose repairs are rebuilds, and it proves the ledger.

alpha (0.7 by default) is the whole contract: a child may hold under
`alpha` of its parent, and a tipped subtree is flattened and rebuilt
midpoint-first in one pass — no rotations, no sizes stored on nodes.
`selftest` keeps that promise on seeded mixed storms: answers equal
bisect's, every rebuild is lossless, and the work counter tracks
n log n while a single insert may still charge linear.
"""

from __future__ import annotations

from .keys import KeyValueError, describe, ensure_key
from .rules import (
    DEFAULT_ALPHA,
    MAX_KEYS,
    RuleError,
    checked_alpha,
    depth_bound,
    heavy_child,
    lower_child,
    violates,
    worst_case_rebuild,
)
from .streams import Snapshot, StreamError, load_keys, synthetic, write_keys
from .tree import Node, ScapegoatTree, TreeError, flatten, height_of, size_of

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_ALPHA",
    "MAX_KEYS",
    "KeyValueError",
    "Node",
    "RuleError",
    "ScapegoatTree",
    "Snapshot",
    "StreamError",
    "TreeError",
    "__version__",
    "checked_alpha",
    "depth_bound",
    "describe",
    "ensure_key",
    "flatten",
    "heavy_child",
    "height_of",
    "load_keys",
    "lower_child",
    "size_of",
    "synthetic",
    "violates",
    "worst_case_rebuild",
    "write_keys",
]

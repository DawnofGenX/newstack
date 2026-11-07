"""Integer keys, height-balanced: the tree and the sort that checks it.

The tree seats integer keys so the in-order walk is always the plain
`sorted(keys)`, every balance factor stays inside -1, 0, 1 after
every insert and every remove, and the height stays under
ceil(1.44 * log2(n + 2)) — checked against the walk, the factor
walk, and the ceiling, never assumed.
"""

from __future__ import annotations

from .brute import brute_sort, factors, height_bound
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_keys,
    synthetic,
    write_keys,
)
from .keys import MAX_KEY, KeysError, ensure_key
from .tree import AVLTree, TreeError

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_KEY",
    "AVLTree",
    "CorpusError",
    "KeysError",
    "Snapshot",
    "TreeError",
    "__version__",
    "brute_sort",
    "ensure_key",
    "factors",
    "height_bound",
    "load_keys",
    "synthetic",
    "write_keys",
]

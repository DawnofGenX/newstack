"""Integer keys, self-adjusting: the tree and the walk that checks it.

The tree seats integer keys so the in-order walk is always the plain
`sorted(keys)`, and every access — insert, lookup, min, max — rides
the touched node to the root with zig, zig-zig, or zig-zag. The
promise is checked against the walk and the raw links, never
assumed: after a hit the touched key sits nowhere else but the root.
"""

from __future__ import annotations

from .brute import brute_sort, is_root
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_keys,
    synthetic,
    write_keys,
)
from .keys import MAX_KEY, KeysError, ensure_key
from .tree import SplayTree, TreeError

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_KEY",
    "CorpusError",
    "KeysError",
    "Snapshot",
    "SplayTree",
    "TreeError",
    "__version__",
    "brute_sort",
    "ensure_key",
    "is_root",
    "load_keys",
    "synthetic",
    "write_keys",
]

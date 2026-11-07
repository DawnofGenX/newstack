"""Integer keys, sifted by hand: push, pop, peek, len.

The parent rides no higher than its children, and the drain order of
any storm must equal the plain `sorted(pushed)`. The promise is
checked against the shipped checker and a plain sort, never assumed:
after every operation the array answers the parent rule with an
empty list, and the head is the minimum of the live bag nowhere else.
"""

from __future__ import annotations

from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_keys,
    synthetic,
    write_keys,
)
from .heap import HeapError, MinHeap
from .keys import MAX_KEY, KeysError, ensure_key
from .oracle import brute_drain, heap_breaks

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_KEY",
    "CorpusError",
    "HeapError",
    "KeysError",
    "MinHeap",
    "Snapshot",
    "__version__",
    "brute_drain",
    "ensure_key",
    "heap_breaks",
    "load_keys",
    "synthetic",
    "write_keys",
]

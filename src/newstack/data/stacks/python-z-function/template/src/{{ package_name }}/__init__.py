"""Lowercase words, honestly cut: the array and the scan that checks it.

The array seats every suffix by the prefix it shares — ``z[i]`` is
the longest common prefix of the word and the word from ``i`` on,
``z[0]`` the whole length — and the derived occurrence list equals
the naive scan's start list, overlaps counted, the empty word
owning the empty array. The promise is checked, never assumed: the
array cannot tell itself from a dumb stepper.
"""

from __future__ import annotations

from .array import (
    SEP,
    ArrayError,
    ZArray,
    occurrences,
    z_function,
)
from .corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_words,
    synthetic,
    write_words,
)
from .naive import lcp_length, naive_count, naive_occurrences, naive_z
from .word import MAX_WORD, WordError, describe, ensure_pattern, ensure_word

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_SEED",
    "MAX_WORD",
    "SEP",
    "ArrayError",
    "CorpusError",
    "Snapshot",
    "WordError",
    "ZArray",
    "__version__",
    "describe",
    "ensure_pattern",
    "ensure_word",
    "lcp_length",
    "load_words",
    "naive_count",
    "naive_occurrences",
    "naive_z",
    "occurrences",
    "synthetic",
    "write_words",
    "z_function",
]

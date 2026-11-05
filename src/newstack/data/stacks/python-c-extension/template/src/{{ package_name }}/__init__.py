"""Text statistics with the hot loop in C.

``count`` is the compiled path. ``reference.count`` is the readable one, and the
tests assert they agree on random input -- including the bytes no fixture
usually contains (vertical tab, form feed, embedded NUL).
"""

from __future__ import annotations

from . import reference
from ._speedups import __version__, count_bytes, count_str, separators

__all__ = [
    "__version__",
    "count",
    "count_bytes",
    "count_str",
    "reference",
    "separators",
]


def count(data: bytes) -> tuple[int, int, int]:
    """(lines, words, bytes) for a bytes-like object."""
    return count_bytes(data)

"""The exponential oracle: bare recursion, no memo, short words only.

This module exists to be wrong in an honest way where ``distance``
could be wrong in a quiet one. It recomputes every branch from
scratch, which is exactly why it is capped at ``ORACLE_LIMIT`` letters
per side; the shipped words in ``distance.SHIPPED`` sit under the cap,
and anything longer is refused by name rather than left to run.
"""

from __future__ import annotations

from .distance import DistanceError
from .words import ensure_text

#: The longest pair, in letters per side, the bare recursion will face.
ORACLE_LIMIT = 8


def oracle_distance(left: object, right: object) -> int:
    """The naive unit-cost recursion, memo-free, for short strings only."""
    a = ensure_text(left)
    b = ensure_text(right)
    if len(a) > ORACLE_LIMIT or len(b) > ORACLE_LIMIT:
        raise DistanceError(
            f"the oracle stands beside {ORACLE_LIMIT} letters at most, "
            f"not {len(a)} and {len(b)}"
        )
    return _recurse(a, b)


def _recurse(a: str, b: str) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)
    if a[0] == b[0]:
        return _recurse(a[1:], b[1:])
    delete = _recurse(a[1:], b) + 1
    insert = _recurse(a, b[1:]) + 1
    replace = _recurse(a[1:], b[1:]) + 1
    return min(delete, insert, replace)

"""The balance rule, its depth promise, and the worst-case rebuild.

alpha is the whole contract: a parent tolerates a child only while the
child's live count stays under `alpha * parent's live count`. Solving
the rule the other direction, a settled tree of n keys sits no deeper
than `depth_bound` reports — a counted promise, never assumed, and
proven on the tree after every insert settles. A deletion only shrinks
the tree, so it cannot deepen it and never fires a rebuild.

A rebuild pays the deepest bill the tree can hand out: flattening a
heaviest tolerated child costs `worst_case_rebuild` node touches.
That is why the counter story settles for O(n log n) over a stream
while one insert may still charge O(n) — the greedy repair is honest
about both ends of its ledger. alpha outside the open unit interval
has no rule to keep, so it is refused.
"""

from __future__ import annotations

import math

__all__ = [
    "DEFAULT_ALPHA",
    "MAX_KEYS",
    "RuleError",
    "checked_alpha",
    "depth_bound",
    "heavy_child",
    "lower_child",
    "violates",
    "worst_case_rebuild",
]

DEFAULT_ALPHA = 0.7
MAX_KEYS = 20_000


class RuleError(ValueError):
    """alpha sits where no balance rule can hold."""


def checked_alpha(alpha: float) -> float:
    """Return alpha once proven to sit inside the open unit interval."""
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)):
        raise RuleError(f"{alpha!r} is not a number")
    if not 0.0 < float(alpha) < 1.0:
        raise RuleError(f"alpha {alpha} sits outside the open unit interval")
    return float(alpha)


def heavy_child(alpha: float, size: int) -> int:
    """The largest child count a parent of `size` tolerates."""
    return math.floor(checked_alpha(alpha) * size)


def lower_child(alpha: float, size: int) -> int:
    """The mirror of the ceiling: where a rebuild lands its children.

    A rebuild splits at the midpoint, and for any parent of at least
    two keys the midpoint clears this floor — which is why rebuild
    output always holds the rule and deletion needs no repair of its
    own: shrinking only carries children further below the ceiling.
    """
    scaled = round((1.0 - checked_alpha(alpha)) * 100)
    return -((-scaled * size) // 100)


def violates(alpha: float, child: int, parent: int) -> bool:
    """True when a child of `child` overshoots what `parent` tolerates."""
    if isinstance(parent, bool) or not isinstance(parent, int) or parent < 1:
        raise RuleError(f"{parent!r} is not a parent count")
    if isinstance(child, bool) or not isinstance(child, int) or child < 0:
        raise RuleError(f"{child!r} is not a child count")
    return child > heavy_child(alpha, parent)


def depth_bound(alpha: float, keys: int) -> int:
    """The floor the rule promises: a settled tree sits no deeper."""
    if isinstance(keys, bool) or not isinstance(keys, int) or keys < 1:
        raise RuleError(f"{keys!r} is not a tree size")
    if keys > MAX_KEYS:
        raise RuleError(f"{keys} exceeds the {MAX_KEYS}-key cap")
    return math.ceil(math.log(keys, 1.0 / checked_alpha(alpha))) + 1


def worst_case_rebuild(alpha: float, keys: int) -> int:
    """The node touches the heaviest tolerated child flattens."""
    if isinstance(keys, bool) or not isinstance(keys, int) or keys < 1:
        raise RuleError(f"{keys!r} is not a tree size")
    return heavy_child(alpha, keys)

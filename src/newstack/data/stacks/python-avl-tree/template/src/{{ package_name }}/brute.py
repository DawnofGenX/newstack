"""The oracles: a plain sort, an honest bound, a factor walk.

Every answer the tree gives must equal what this module answers on
the same keys. The order is `sorted(keys)` with no cleverness at all;
the ceiling is `ceil(1.44 * log2(n + 2))`; the walk recomputes every
balance factor from raw heights, so the tree cannot grade its own
homework.

```text
the sorted list, the bound, and the walk are the sentence
the tree is compared against.
```
"""

from __future__ import annotations

import math
from typing import Any


def brute_sort(keys: Any) -> list[int]:
    """The keys in plain sorted order, the answer every walk owes."""
    return sorted(keys)


def height_bound(count: int) -> int:
    """ceil(1.44 * log2(n + 2)) — the AVL ceiling on tree height."""
    if count < 0:
        raise ValueError(f"no bound from {count} keys")
    return math.ceil(1.44 * math.log2(count + 2))


def _true_height(node: Any) -> int:
    """Height from raw structure, ignoring any stored figure."""
    if node is None:
        return 0
    return 1 + max(_true_height(node.left), _true_height(node.right))


def factors(root: Any) -> list[int]:
    """Every balance factor in the tree, recomputed from structure.

    The walk descends the whole tree, so a stale stored height or a
    flipped factor anywhere shows up here as a number outside
    -1, 0, 1 — checked, never assumed.
    """
    if root is None:
        return []
    left = _true_height(root.left)
    right = _true_height(root.right)
    return [left - right, *factors(root.left), *factors(root.right)]

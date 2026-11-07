"""The oracles: a plain sort and the seat a touched key must reach.

Every answer the tree gives must equal what this module answers on
the same keys. The order is `sorted(keys)` with no cleverness at
all; the root is the key the last-touched node must ride to, so the
splay promise is checked against structure, never assumed. The tree
cannot grade its own homework from here.
"""

from __future__ import annotations

from typing import Any


def brute_sort(keys: Any) -> list[int]:
    """The keys in plain sorted order, the answer every walk owes."""
    return sorted(keys)


def root_key(node: Any) -> int | None:
    """The key sitting at a root, or None for nothing."""
    return None if node is None else node.key


def is_root(tree: Any, key: object) -> bool:
    """Whether the key sits at the tree's root — the splay promise.

    The storm and the selftest both ask this after every access:
    a lookup that admitted a key left it nowhere else but the root.
    """
    root = getattr(tree, "_root", None)
    return root is not None and root.key == key

"""The two wrong trees, kept so the demo can measure what they cost.

Neither of these is used by the package. Both are what a first draft looks like,
and the point of the stack is that the difference is measurable.
"""

from __future__ import annotations

from .hashing import bare_leaf, bare_node, leaf_hash, node_hash, sha256


def bare_root(leaves: list[bytes]) -> bytes:
    """A tree with no domain prefix: a leaf and a node are hashed the same way."""
    if not leaves:
        return sha256(b"")
    level = [bare_leaf(item) for item in leaves]
    while len(level) > 1:
        merged: list[bytes] = []
        for position in range(0, len(level) - 1, 2):
            merged.append(bare_node(level[position], level[position + 1]))
        if len(level) % 2:
            merged.append(level[-1])
        level = merged
    return level[0]


def duplicate_root(leaves: list[bytes]) -> bytes:
    """A tree that duplicates the last node of an odd level (the Bitcoin shape).

    For five leaves this is `H(H(H(a, b), H(c, d)), H(e, e))`, while the RFC
    splits at four and gets `H(H(H(a, b), H(c, d)), H(e))`. Two rules, two roots,
    for the same five leaves.
    """
    if not leaves:
        return sha256(b"")
    level = [leaf_hash(item) for item in leaves]
    while len(level) > 1:
        merged: list[bytes] = []
        for position in range(0, len(level) - 1, 2):
            merged.append(node_hash(level[position], level[position + 1]))
        if len(level) % 2:
            merged.append(node_hash(level[-1], level[-1]))
        level = merged
    return level[0]


def forgery(leaves: list[bytes]) -> dict[str, object]:
    """Present the pair of child digests as a leaf, and see which tree believes it.

    With no domain prefix, `sha256(left || right)` is both the node's digest and
    the digest of a leaf whose content is `left || right`, so a one-leaf tree
    over that content has the same root as the two-leaf tree. The prefix makes
    the two inputs different, and the forgery stops working.
    """
    left, right = bare_leaf(leaves[0]), bare_leaf(leaves[1])
    forged = left + right
    return {
        "two_leaf_bare_root": bare_node(left, right),
        "forged_bare_root": bare_leaf(forged),
        "forged_prefixed_root": leaf_hash(forged),
        "two_leaf_prefixed_root": node_hash(leaf_hash(leaves[0]), leaf_hash(leaves[1])),
        "forged_leaf_bytes": len(forged),
    }

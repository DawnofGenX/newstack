"""Two hashes, because one hash cannot tell a leaf from a node.

A Merkle tree hashes leaves and internal nodes with the same function unless it
is told not to. Then a node's digest is a valid leaf digest, and anybody can
present the pair of child digests as a leaf: the tree happily recomputes the
same root for a document set that never existed. The domain prefix is what makes
those two inputs different lengths of the same input space.
"""

from __future__ import annotations

import hashlib

LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"
HASH_BYTES = 32


class HashError(ValueError):
    """A hash is not the shape this module produces."""


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def leaf_hash(data: bytes) -> bytes:
    """The hash of a leaf, prefixed so it can never equal a node's hash."""
    return sha256(LEAF_PREFIX + data)


def node_hash(left: bytes, right: bytes) -> bytes:
    if len(left) != HASH_BYTES or len(right) != HASH_BYTES:
        raise HashError(
            f"a node needs two {HASH_BYTES}-byte children, not {len(left)} and {len(right)}"
        )
    return sha256(NODE_PREFIX + left + right)


def bare_leaf(data: bytes) -> bytes:
    """The unprefixed leaf hash, kept only so the demo can show the forgery."""
    return sha256(data)


def bare_node(left: bytes, right: bytes) -> bytes:
    """The unprefixed node hash, kept only so the demo can show the forgery."""
    return sha256(left + right)


def hex_of(digest: bytes) -> str:
    return digest.hex()


def unhex(text: str) -> bytes:
    try:
        digest = bytes.fromhex(text.strip())
    except ValueError as error:
        raise HashError(f"'{text}' is not hexadecimal: {error}") from error
    if len(digest) != HASH_BYTES:
        raise HashError(f"'{text}' is {len(digest)} byte(s), not {HASH_BYTES}")
    return digest

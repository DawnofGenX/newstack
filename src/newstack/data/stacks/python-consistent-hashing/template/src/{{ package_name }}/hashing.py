"""One hash, one width, no surprises."""

from __future__ import annotations

import hashlib

WIDTH = 1 << 64


def hash64(text: str) -> int:
    """A 64-bit hash of ``text``.

    blake2b with an 8-byte digest: stable across runs and processes, unlike ``hash()``, which
    is salted per interpreter and would put every key on a different node after a restart.
    """
    digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def virtual_node_key(node: str, index: int) -> str:
    """The text hashed for the ``index``-th virtual node of ``node``.

    The separator matters: ``node + str(index)`` makes ``("a1", 2)`` and ``("a", 12)`` collide.
    """
    return f"{node}#{index}"


def mod_slot(key: str, slots: int) -> int:
    """The naive placement: ``hash(key) % slots``."""
    if slots < 1:
        raise ValueError("slots must be at least 1")
    return hash64(key) % slots

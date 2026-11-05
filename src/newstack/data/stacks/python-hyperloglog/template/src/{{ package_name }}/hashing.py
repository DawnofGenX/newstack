"""The hash every register index and rank is derived from."""

from __future__ import annotations

from hashlib import blake2b

BITS = 64


def hash64(text: str) -> int:
    """A stable 64-bit hash.

    ``hash()`` is salted per interpreter, so a sketch built in one process would
    not be mergeable with one built in another. blake2b is the same everywhere.
    """
    if not isinstance(text, str):
        raise TypeError(f"hash64 expects a string, not {type(text).__name__}")
    digest = blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def hash64_biased(text: str) -> int:
    """The wrong hash on purpose: the low bits of the digest.

    Real entropy is spread over the whole digest, but a stream of small integers
    hashed this way keeps its structure in the high bits, and a sketch that reads
    its index from the low bits then puts correlated items in one register.
    """
    digest = blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest[:4].ljust(8, b"\x00"), "big")

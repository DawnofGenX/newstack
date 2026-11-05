"""Where a user lands, in integers, forever.

`hash()` is not usable here: Python randomises string hashing per process, so a rollout written with
it would move every user on every restart. SHA-256 does not.
"""

from __future__ import annotations

import hashlib

from .model import BPS


def bucket_of(salt: str, user: str) -> int:
    """The user's bucket for this salt: stable across processes, machines and Python versions."""
    if not user:
        raise ValueError("user must be a non-empty string")
    if not salt:
        raise ValueError("salt must be a non-empty string; it is what makes two flags independent")
    digest = hashlib.sha256(f"{salt}:{user}".encode()).hexdigest()
    return int(digest[:8], 16) % BPS


def inside(salt: str, user: str, rollout: int) -> bool:
    """True when the user is inside a rollout of `rollout` percent.

    The comparison is `<` against a cutoff in basis points, so 0 admits nobody and 100 admits
    everybody — an off-by-one that a `<=` would hide at exactly 0%.
    """
    if not 0 <= rollout <= 100:
        raise ValueError(f"rollout must be between 0 and 100, got {rollout}")
    return bucket_of(salt, user) < rollout * (BPS // 100)


def spread(salt: str, users: list[str]) -> dict[int, int]:
    """How many users landed in each of the hundred percent-buckets. Used by `distribution`."""
    counts = dict.fromkeys(range(100), 0)
    for user in users:
        counts[bucket_of(salt, user) // (BPS // 100)] += 1
    return counts

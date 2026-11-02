"""Core helpers for {{ title }}."""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"[A-Za-z0-9']+")


def word_count(text: str) -> int:
    """Return the number of words in *text*."""
    return len(_WORD_RE.findall(text))


def truncate(text: str, limit: int, suffix: str = "…") -> str:
    """Shorten *text* to at most *limit* characters, appending *suffix* when cut."""
    if limit < 0:
        raise ValueError("limit must be >= 0")
    if len(text) <= limit:
        return text
    if limit <= len(suffix):
        return suffix[:limit]
    return text[: limit - len(suffix)].rstrip() + suffix

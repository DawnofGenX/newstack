"""Measuring a filter is the only way to know what it does."""

from __future__ import annotations

from .bloom import Bloom, CountingBloom

PROBES = 20_000


def false_positive_rate(bloom: Bloom | CountingBloom, probes: int = PROBES) -> float:
    """Probe items that were never added; every yes is a false positive."""
    hits = 0
    for number in range(probes):
        if bloom.might_contain(f"absent-{number}"):
            hits += 1
    return hits / probes


def false_negatives(bloom: Bloom | CountingBloom, items: list[str]) -> list[str]:
    """Every added item must answer yes. Anything else is a broken filter."""
    return [item for item in items if not bloom.might_contain(item)]


def fill(bloom: Bloom | CountingBloom) -> float:
    return bloom.fill()

"""What moved, and whether it had any business moving."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from .hashing import mod_slot


class AuditError(ValueError):
    """Two maps that cannot be compared."""


@dataclass(frozen=True)
class Move:
    key: str
    before: str
    after: str

    def line(self) -> str:
        return f"{self.key:<24} {self.before:<10} -> {self.after}"


def moved(before: Mapping[str, str], after: Mapping[str, str]) -> list[Move]:
    """Every key whose owner changed, in key order."""
    missing = set(before) ^ set(after)
    if missing:
        raise AuditError(
            f"the two maps cover different keys ({len(missing)} differ); "
            "comparing them would report noise as movement"
        )
    return [
        Move(key, before[key], after[key])
        for key in sorted(before)
        if before[key] != after[key]
    ]


def percentage(count: int, total: int) -> float:
    return 0.0 if total == 0 else 100.0 * count / total


def summary(before: Mapping[str, str], after: Mapping[str, str]) -> str:
    changes = moved(before, after)
    return (
        f"{len(changes)} of {len(before)} key(s) moved "
        f"({percentage(len(changes), len(before)):.1f}%)"
    )


def only_from(changes: Iterable[Move], node: str) -> bool:
    """True when every move took a key away from ``node`` and nothing else."""
    return all(change.before == node for change in changes)


def mod_map(keys: Iterable[str], nodes: list[str]) -> dict[str, str]:
    """The comparison: ``hash(key) % len(nodes)``."""
    if not nodes:
        raise AuditError("no nodes to place keys on")
    return {key: nodes[mod_slot(key, len(nodes))] for key in keys}


def histogram(mapping: Mapping[str, str]) -> dict[str, int]:
    counted = Counter(mapping.values())
    return dict(sorted(counted.items()))

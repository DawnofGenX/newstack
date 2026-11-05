"""The three laws a state-based CRDT has to satisfy, checked on real states."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

Merge = Callable[[Any, Any], Any]
Serialise = Callable[[Any], str]


@dataclass(frozen=True)
class Law:
    """One law, and the states that broke it if any did."""

    name: str
    held: bool
    detail: str

    def line(self) -> str:
        mark = "ok  " if self.held else "FAIL"
        return f"  {mark}  {self.name:<12}  {self.detail}"


def _same(left: Any, right: Any, serialise: Serialise) -> bool:
    return serialise(left) == serialise(right)


def check(states: Sequence[Any], merge: Merge, serialise: Serialise) -> list[Law]:
    """Idempotent, commutative and associative over every state and pair given."""
    items = list(states)
    if len(items) < 2:
        raise ValueError("law checks need at least two states")
    results: list[Law] = []

    broken = [
        index
        for index, state in enumerate(items)
        if not _same(merge(state, state), state, serialise)
    ]
    if broken:
        detail = f"merging these states with themselves changed them: {broken}"
        results.append(Law("idempotent", False, detail))
    else:
        results.append(Law("idempotent", True, "merge(x, x) is x for every state"))

    pairs = [(left, right) for left in range(len(items)) for right in range(left + 1, len(items))]
    backwards = [
        (left, right)
        for left, right in pairs
        if not _same(merge(items[left], items[right]), merge(items[right], items[left]), serialise)
    ]
    if backwards:
        results.append(Law("commutative", False, f"order mattered for the pairs {backwards}"))
    else:
        results.append(
            Law("commutative", True, f"merge(a, b) is merge(b, a) for {len(pairs)} pairs")
        )

    triples = [
        (first, second, third)
        for first in range(len(items))
        for second in range(len(items))
        for third in range(len(items))
    ]
    regrouped = [
        (first, second, third)
        for first, second, third in triples
        if not _same(
            merge(merge(items[first], items[second]), items[third]),
            merge(items[first], merge(items[second], items[third])),
            serialise,
        )
    ]
    if regrouped:
        results.append(Law("associative", False, f"grouping mattered for the triples {regrouped}"))
    else:
        results.append(
            Law("associative", True, f"grouping never mattered for {len(triples)} triples")
        )
    return results

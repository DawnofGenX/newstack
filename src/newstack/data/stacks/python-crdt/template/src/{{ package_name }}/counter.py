"""Counters that converge; the signed variant exists to be proven wrong."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class CounterError(ValueError):
    """A counter state that cannot mean what it says."""


def _counts(payload: object, label: str) -> dict[str, int]:
    if not isinstance(payload, dict):
        raise CounterError(f"{label} must map node names to counts, not {payload!r}")
    cleaned: dict[str, int] = {}
    for node, count in payload.items():
        if not isinstance(node, str) or not node:
            raise CounterError(f"{label} has an empty node name")
        if isinstance(count, bool) or not isinstance(count, int):
            raise CounterError(f"{label} count for {node!r} must be an integer, not {count!r}")
        if count < 0:
            raise CounterError(
                f"{label} count for {node!r} is {count}; a grow-only counter never goes "
                "down, and a negative number here means the state was edited by hand"
            )
        cleaned[node] = count
    return cleaned


def _positive(by: object, label: str) -> int:
    if isinstance(by, bool) or not isinstance(by, int) or by < 1:
        raise CounterError(f"{label} must be a positive integer, not {by!r}")
    return by


def _kind(payload: object, expected: str) -> dict[Any, Any]:
    if not isinstance(payload, dict):
        raise CounterError(f"a {expected} state is a JSON object, not {payload!r}")
    kind = payload.get("type")
    if kind != expected:
        raise CounterError(f"this is a {kind!r} state, not a {expected!r} one")
    return payload


@dataclass(frozen=True)
class GCounter:
    """A grow-only counter: each node owns one entry, so merge is a pointwise max."""

    counts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "counts", _counts(self.counts, "g-counter"))

    @classmethod
    def empty(cls) -> GCounter:
        return cls()

    def increment(self, node: str, by: int = 1) -> GCounter:
        by = _positive(by, "the increment")
        if not isinstance(node, str) or not node:
            raise CounterError("an increment needs a node: an anonymous count cannot be merged")
        return GCounter({**self.counts, node: self.counts.get(node, 0) + by})

    def value(self) -> int:
        return sum(self.counts.values())

    def merge(self, other: GCounter) -> GCounter:
        names = set(self.counts) | set(other.counts)
        return GCounter(
            {name: max(self.counts.get(name, 0), other.counts.get(name, 0)) for name in names}
        )

    def as_dict(self) -> dict[str, Any]:
        return {"type": "g-counter", "counts": dict(sorted(self.counts.items()))}

    @classmethod
    def parse(cls, payload: object) -> GCounter:
        body = _kind(payload, "g-counter")
        return cls(_counts(body.get("counts"), "g-counter"))


@dataclass(frozen=True)
class SignedTotal:
    """The wrong way: one dict of signed counts merged with max.

    It looks like a counter and converges, but max() cannot tell two concurrent
    decrements from one, so the total it reports is a lower bound, not the total.
    """

    counts: dict[str, int] = field(default_factory=dict)

    def apply(self, node: str, delta: int) -> SignedTotal:
        if not isinstance(node, str) or not node:
            raise CounterError("a change needs a node name")
        if isinstance(delta, bool) or not isinstance(delta, int) or delta == 0:
            raise CounterError(f"a change must be a non-zero integer, not {delta!r}")
        return SignedTotal({**self.counts, node: self.counts.get(node, 0) + delta})

    def merge(self, other: SignedTotal) -> SignedTotal:
        names = set(self.counts) | set(other.counts)
        return SignedTotal(
            {name: max(self.counts.get(name, 0), other.counts.get(name, 0)) for name in names}
        )

    def value(self) -> int:
        return sum(self.counts.values())

    def as_dict(self) -> dict[str, Any]:
        return {"type": "signed-total", "counts": dict(sorted(self.counts.items()))}


@dataclass(frozen=True)
class PNCounter:
    """Two grow-only counters. Decrements never erase each other, because they add up."""

    positive: GCounter = field(default_factory=GCounter)
    negative: GCounter = field(default_factory=GCounter)

    @classmethod
    def empty(cls) -> PNCounter:
        return cls()

    def increment(self, node: str, by: int = 1) -> PNCounter:
        return PNCounter(self.positive.increment(node, by), self.negative)

    def decrement(self, node: str, by: int = 1) -> PNCounter:
        return PNCounter(self.positive, self.negative.increment(node, by))

    def value(self) -> int:
        return self.positive.value() - self.negative.value()

    def merge(self, other: PNCounter) -> PNCounter:
        return PNCounter(self.positive.merge(other.positive), self.negative.merge(other.negative))

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": "pn-counter",
            "positive": self.positive.as_dict()["counts"],
            "negative": self.negative.as_dict()["counts"],
        }

    @classmethod
    def parse(cls, payload: object) -> PNCounter:
        body = _kind(payload, "pn-counter")
        try:
            positive = GCounter(_counts(body.get("positive"), "pn-counter positive"))
            negative = GCounter(_counts(body.get("negative"), "pn-counter negative"))
        except CounterError as error:
            raise CounterError(f"pn-counter: {error}") from error
        return cls(positive, negative)

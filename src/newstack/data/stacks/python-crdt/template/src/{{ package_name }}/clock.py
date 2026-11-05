"""Stamps that order writes without ever reading the clock twice."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ClockError(ValueError):
    """A stamp that cannot order anything."""


@dataclass(frozen=True, order=True)
class Stamp:
    """A total order over writes: milliseconds first, node name as the tiebreak."""

    at_ms: int
    node: str

    def __post_init__(self) -> None:
        if isinstance(self.at_ms, bool) or not isinstance(self.at_ms, int):
            raise ClockError(f"a stamp needs milliseconds as an integer, not {self.at_ms!r}")
        if self.at_ms < 0:
            raise ClockError("a stamp before the epoch cannot order writes")
        if not isinstance(self.node, str) or not self.node:
            raise ClockError(
                "a stamp needs a node: two nodes writing in the same millisecond "
                "must still sort, or the merge is a coin toss"
            )

    @property
    def text(self) -> str:
        return f"{self.at_ms}@{self.node}"

    def as_list(self) -> list[Any]:
        return [self.at_ms, self.node]

    @classmethod
    def parse(cls, payload: object) -> Stamp:
        if not isinstance(payload, list) or len(payload) != 2:
            raise ClockError(f"a stamp is [milliseconds, node], not {payload!r}")
        return cls(payload[0], payload[1])  # type: ignore[arg-type]

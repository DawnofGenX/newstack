"""A register with one winner, and an honest account of the write it drops."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .clock import ClockError, Stamp


class RegisterError(ValueError):
    """A register write that has no defensible answer."""


@dataclass(frozen=True)
class Write:
    """What an assignment did to the value that was already there."""

    applied: bool
    previous: Stamp | None

    def line(self, node_at: Stamp) -> str:
        if not self.applied:
            return f"ignored {node_at.text}: the register already holds a newer write"
        if self.previous is None:
            return "applied, the register was empty"
        return f"applied, dropping the write stamped {self.previous.text}"


@dataclass(frozen=True)
class LWWRegister:
    """Last write wins, where last means the highest (millisecond, node) stamp."""

    value: Any = None
    stamp: Stamp | None = None

    def __post_init__(self) -> None:
        if (self.value is None) != (self.stamp is None):
            raise RegisterError(
                "a register needs a value and a stamp or neither; one without the other "
                "cannot be ordered against anything"
            )

    @property
    def is_empty(self) -> bool:
        return self.stamp is None

    def assign(self, value: Any, at_ms: int, node: str) -> tuple[LWWRegister, Write]:
        stamp = Stamp(at_ms, node)
        if self.stamp is None:
            return LWWRegister(value, stamp), Write(True, None)
        if stamp > self.stamp:
            return LWWRegister(value, stamp), Write(True, self.stamp)
        return self, Write(False, self.stamp)

    def merge(self, other: LWWRegister) -> LWWRegister:
        if self.stamp is None:
            return other
        if other.stamp is None:
            return self
        if self.stamp == other.stamp:
            if self.value != other.value:
                raise RegisterError(
                    f"two writes claim the stamp {self.stamp.text} with different values; "
                    "a stamp is supposed to identify one write"
                )
            return self
        return self if self.stamp > other.stamp else other

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": "lww-register",
            "value": self.value,
            "stamp": self.stamp.as_list() if self.stamp else None,
        }

    @classmethod
    def parse(cls, payload: object) -> LWWRegister:
        if not isinstance(payload, dict) or payload.get("type") != "lww-register":
            raise RegisterError(f"not a lww-register state: {payload!r}")
        stamp = payload.get("stamp")
        try:
            return cls(payload.get("value"), None if stamp is None else Stamp.parse(stamp))
        except ClockError as error:
            raise RegisterError(f"lww-register: {error}") from error

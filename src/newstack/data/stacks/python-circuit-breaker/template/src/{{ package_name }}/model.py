"""The vocabulary of a circuit breaker: three states, one decision, one tally."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class State(StrEnum):
    """The three states are the whole state machine; there is no fourth."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class OpenError(RuntimeError):
    """Raised by `call()` when the breaker refuses to send the request at all."""

    def __init__(self, decision: Decision) -> None:
        super().__init__(decision.reason)
        self.decision = decision

    @property
    def retry_in(self) -> float:
        return self.decision.retry_in


@dataclass(frozen=True, slots=True)
class Decision:
    """What `allow()` answers: yes or no, why, and (when no) how long until it changes."""

    allowed: bool
    state: State
    reason: str
    retry_in: float = 0.0

    def line(self) -> str:
        verdict = "allow" if self.allowed else "deny "
        suffix = f" retry_in={self.retry_in:.1f}s" if self.retry_in else ""
        return f"{verdict} {self.state:<9} {self.reason}{suffix}"


@dataclass(slots=True)
class Tally:
    """Counters are part of the product: a breaker nobody can observe gets removed."""

    requests: int = 0
    allowed: int = 0
    denied: int = 0
    successes: int = 0
    failures: int = 0
    ignored: int = 0
    late: int = 0
    trips: int = 0
    probes: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "requests": self.requests,
            "allowed": self.allowed,
            "denied": self.denied,
            "successes": self.successes,
            "failures": self.failures,
            "ignored": self.ignored,
            "late": self.late,
            "trips": self.trips,
            "probes": self.probes,
        }

"""A scripted outage, printed as a timeline.

The demo exists because a breaker is easier to trust when you can read the sequence: three
failures, a trip, a refusal that never touched the network, a cooldown, one probe, recovery.
Every decision below comes from the real `Breaker`; only the clock is fake.
"""

from __future__ import annotations

from dataclasses import dataclass

from .breaker import Breaker
from .clock import FakeClock
from .model import Decision, State


@dataclass(frozen=True, slots=True)
class Step:
    at: float
    label: str
    decision: Decision
    state: State

    def line(self) -> str:
        return f"t={self.at:6.1f}  {self.label:<22}  {self.decision.line()}"


@dataclass(frozen=True, slots=True)
class Timeline:
    steps: tuple[Step, ...]
    ok: bool

    def lines(self) -> list[str]:
        return [step.line() for step in self.steps]

    def summary(self) -> list[str]:
        first = self.steps[0].state if self.steps else State.CLOSED
        last = self.steps[-1].state if self.steps else State.CLOSED
        return [
            f"start     {first}",
            f"end       {last}",
            f"verdict   {'recovered' if self.ok else 'did not recover'}",
        ]


def run(failures: int = 3, cooldown: float = 30.0, successes: int = 2) -> Timeline:
    """Drive a breaker through one outage and one recovery, then check it did what it says."""
    if failures < 1:
        raise ValueError("failures must be at least 1")
    if successes < 1:
        raise ValueError("successes must be at least 1")
    clock = FakeClock()
    breaker = Breaker(failure_threshold=failures, cooldown_s=cooldown, clock=clock)
    steps: list[Step] = []

    def step(label: str, decision: Decision) -> None:
        steps.append(Step(clock.now(), label, decision, breaker.state))

    for index in range(successes):
        step(f"call {index + 1} ok", breaker.allow())
        breaker.record_success()

    for index in range(failures):
        step(f"failure {index + 1}", breaker.allow())
        breaker.record_failure(RuntimeError("503 from upstream"))

    step("call while open", breaker.allow())

    clock.advance(cooldown / 2)
    step("half the cooldown", breaker.allow())

    clock.advance(cooldown / 2)
    step("cooldown over", breaker.allow())
    breaker.record_success()

    step("call after recovery", breaker.allow())
    breaker.record_success()

    states = [step.state for step in steps]
    ok = (
        State.OPEN in states
        and states[-1] is State.CLOSED
        and not steps[failures + successes].decision.allowed
        and not steps[failures + successes + 1].decision.allowed
        and steps[failures + successes + 2].decision.allowed
        and breaker.tally.denied == 2
        and breaker.tally.probes == 1
        and breaker.tally.trips == 1
    )
    return Timeline(tuple(steps), ok)

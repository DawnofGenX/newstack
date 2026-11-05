"""A booking saga you can watch unwind.

Three steps, each with an obvious real-world compensating action, and a record
of the order the calls were made in -- which is the only interesting thing to
look at when a rollback goes wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .runner import Saga, Step


class Declined(RuntimeError):
    """The payment provider said no."""


@dataclass
class Calls:
    """The order things happened in, for printing and for tests."""

    names: list[str] = field(default_factory=list)
    refunds: int = 0
    failures: dict[str, int] = field(default_factory=dict)

    def record(self, name: str) -> None:
        self.names.append(name)

    def fail_once(self, name: str) -> None:
        """Raise the first time ``name`` is recorded, then let it through."""
        seen = self.failures.get(name, 0)
        self.failures[name] = seen + 1
        if seen == 0:
            raise Declined(f"{name} failed on purpose (attempt {seen + 1})")


def build(
    journal_path: str | Path,
    *,
    decline_at: str | None = None,
    break_compensation: str | None = None,
    flaky_compensation: str | None = None,
    saga_id: str = "book-trip",
    calls: Calls | None = None,
) -> Saga:
    """Assemble the booking saga, with knobs for the three interesting failures."""
    log = calls if calls is not None else Calls()

    def forward(name: str) -> Any:
        def run(context: Any) -> str:
            log.record(name)
            if decline_at == name:
                log.fail_once(name)
                raise Declined(f"{name} was declined by the provider")
            return context.key

        return run

    def backward(name: str, label: str) -> Any:
        def undo(context: Any) -> None:
            log.record(label)
            if break_compensation == name:
                raise Declined(f"{label} keeps failing; the provider is down")
            if flaky_compensation == name:
                log.fail_once(label)
            if label == "refund-card":
                log.refunds += 1

        return undo

    steps = [
        Step(
            name="reserve-hotel",
            action=forward("reserve-hotel"),
            compensation=backward("reserve-hotel", "release-hotel"),
        ),
        Step(
            name="charge-card",
            action=forward("charge-card"),
            compensation=backward("charge-card", "refund-card"),
            max_attempts=2,
        ),
        Step(
            name="book-flight",
            action=forward("book-flight"),
            compensation=backward("book-flight", "cancel-flight"),
        ),
    ]
    return Saga(saga_id, steps, Path(journal_path), state={"calls": log})


def scenarios(directory: str | Path) -> list[tuple[str, Any]]:
    """The three stories the demo tells, each with its own journal file."""
    root = Path(directory)
    return [
        ("everything works", lambda: build(root / "happy.jsonl")),
        (
            "the flight is declined",
            lambda: build(root / "declined.jsonl", decline_at="book-flight"),
        ),
        (
            "the refund endpoint is down",
            lambda: build(
                root / "stuck.jsonl", decline_at="book-flight", break_compensation="charge-card"
            ),
        ),
        (
            "the refund fails once, then works",
            lambda: build(
                root / "flaky.jsonl", decline_at="book-flight", flaky_compensation="charge-card"
            ),
        ),
    ]

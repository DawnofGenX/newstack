"""The report format, in one place, so the writer and the reader cannot drift.

Durations are milliseconds on purpose: a report in seconds with three decimals is
where the 40 ms test and the 400 ms test become the same number to a tired reader.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

FORMAT = 1
PHASES = ("setup", "call", "teardown")
OUTCOMES = ("passed", "failed", "skipped", "error")


class InputError(Exception):
    """The file is not a report this tool understands."""


@dataclass(frozen=True)
class Phase:
    outcome: str
    duration_ms: float


@dataclass(frozen=True)
class TestRecord:
    nodeid: str
    outcome: str
    duration_ms: float
    tickets: tuple[str, ...] = ()
    phases: dict[str, Phase] = field(default_factory=dict)

    @property
    def ticket(self) -> str:
        return self.tickets[0] if self.tickets else "-"

    def slowest_phase(self) -> str:
        if not self.phases:
            return "-"
        return max(self.phases.items(), key=lambda item: item[1].duration_ms)[0]


@dataclass(frozen=True)
class Report:
    exit_status: int
    tests: tuple[TestRecord, ...]

    def counts(self) -> dict[str, int]:
        counted = Counter(test.outcome for test in self.tests)
        return {name: counted.get(name, 0) for name in OUTCOMES}

    def slowest(self, limit: int = 5) -> list[TestRecord]:
        # Ties break on the nodeid so two runs of the same suite print the same order.
        return sorted(self.tests, key=lambda test: (-test.duration_ms, test.nodeid))[:limit]

    def over(self, threshold_ms: float) -> list[TestRecord]:
        return [test for test in self.tests if test.duration_ms > threshold_ms]

    def as_dict(self) -> dict[str, Any]:
        return {
            "format": FORMAT,
            "exit_status": self.exit_status,
            "tests": [
                {
                    "nodeid": test.nodeid,
                    "outcome": test.outcome,
                    "duration_ms": test.duration_ms,
                    "tickets": list(test.tickets),
                    "phases": {
                        name: {"outcome": phase.outcome, "duration_ms": phase.duration_ms}
                        for name, phase in test.phases.items()
                    },
                }
                for test in self.tests
            ],
        }

    @classmethod
    def from_dict(cls, data: Any) -> Report:
        if not isinstance(data, dict):
            raise InputError("the report must be a JSON object")
        version = data.get("format")
        if version != FORMAT:
            raise InputError(f"unsupported report format {version!r}, expected {FORMAT}")
        raw_tests = data.get("tests")
        if not isinstance(raw_tests, list):
            raise InputError("the report has no tests list")
        return cls(
            exit_status=_integer(data, "exit_status", "the report"),
            tests=tuple(_test(entry, index) for index, entry in enumerate(raw_tests)),
        )


def _integer(container: Any, key: str, where: str) -> int:
    value = container.get(key) if isinstance(container, dict) else None
    if not isinstance(value, int) or isinstance(value, bool):
        raise InputError(f"{where} has no integer {key}")
    return value


def _number(container: Any, key: str, where: str) -> float:
    value = container.get(key) if isinstance(container, dict) else None
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise InputError(f"{where} has no numeric {key}")
    return float(value)


def _test(entry: Any, index: int) -> TestRecord:
    where = f"test {index}"
    if not isinstance(entry, dict):
        raise InputError(f"{where} is not an object")
    nodeid = entry.get("nodeid")
    if not isinstance(nodeid, str) or not nodeid:
        raise InputError(f"{where} has no nodeid")
    outcome = entry.get("outcome")
    if outcome not in OUTCOMES:
        raise InputError(f"{where} ({nodeid}) has outcome {outcome!r}, expected one of {OUTCOMES}")
    tickets = entry.get("tickets", [])
    if not isinstance(tickets, list) or not all(isinstance(ticket, str) for ticket in tickets):
        raise InputError(f"{where} ({nodeid}) has tickets that are not a list of strings")
    raw_phases = entry.get("phases", {})
    if not isinstance(raw_phases, dict):
        raise InputError(f"{where} ({nodeid}) has phases that are not an object")
    phases = {
        name: Phase(
            outcome=str(raw.get("outcome", "?")),
            duration_ms=_number(raw, "duration_ms", where),
        )
        for name, raw in raw_phases.items()
        if isinstance(raw, dict)
    }
    return TestRecord(
        nodeid=nodeid,
        outcome=outcome,
        duration_ms=_number(entry, "duration_ms", where),
        tickets=tuple(tickets),
        phases=phases,
    )


def load(path: Path) -> Report:
    try:
        text = path.read_text()
    except OSError as error:
        raise InputError(f"cannot read {path}: {error.strerror or error}") from error
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise InputError(f"{path} is not JSON: {error}") from error
    return Report.from_dict(data)


def save(path: Path, report: Report) -> None:
    path.write_text(json.dumps(report.as_dict(), indent=2) + "\n")

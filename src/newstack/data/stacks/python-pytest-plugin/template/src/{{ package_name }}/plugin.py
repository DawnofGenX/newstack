"""The pytest plugin. The report is the product; the assertions are the payload.

Every hook here exists because pytest's own output is not a data structure: it is
text on a terminal, it is gone when the terminal closes, and it cannot be diffed
between two commits.
"""

from __future__ import annotations

import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from . import model

REPORT_OPTION = "--testmeta-report"
STRICT_OPTION = "--testmeta-strict"
TICKET_MARKER = "ticket"

class Recorder:
    """Collects phases as the run happens; builds frozen records only at the end."""

    def __init__(self) -> None:
        self.phases: dict[str, dict[str, model.Phase]] = {}
        self.tickets: dict[str, tuple[str, ...]] = {}

    def remember_tickets(self, nodeid: str, tickets: tuple[str, ...]) -> None:
        self.tickets[nodeid] = tickets

    def add_phase(self, nodeid: str, when: str, phase: model.Phase) -> None:
        self.phases.setdefault(nodeid, {})[when] = phase

    def build(self, exit_status: int) -> model.Report:
        tests = []
        for nodeid in sorted(self.phases):
            phases = self.phases[nodeid]
            total = round(sum(phase.duration_ms for phase in phases.values()), 3)
            tests.append(
                model.TestRecord(
                    nodeid=nodeid,
                    outcome=outcome_of(phases),
                    duration_ms=total,
                    tickets=self.tickets.get(nodeid, ()),
                    phases=dict(phases),
                )
            )
        return model.Report(exit_status=exit_status, tests=tuple(tests))


RECORDER: pytest.StashKey[Recorder] = pytest.StashKey()


def outcome_of(phases: dict[str, model.Phase]) -> str:
    """A failure in setup or teardown is an error, not a failed assertion."""
    failed = [name for name, phase in phases.items() if phase.outcome == "failed"]
    if failed:
        return "failed" if "call" in failed else "error"
    if any(phase.outcome == "skipped" for phase in phases.values()):
        return "skipped"
    return "passed"


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("testmeta", "test metadata report")
    group.addoption(
        REPORT_OPTION,
        action="store",
        dest="testmeta_report",
        default=None,
        metavar="PATH",
        help="write a JSON report of every test's phases to PATH",
    )
    group.addoption(
        STRICT_OPTION,
        action="store_true",
        dest="testmeta_strict",
        default=False,
        help="refuse to run a suite in which any test lacks a ticket marker",
    )


def pytest_configure(config: pytest.Config) -> None:
    # --strict-markers turns an unregistered marker into a hard error, so this line,
    # not the decorator, is what makes @pytest.mark.ticket usable in a strict project.
    config.addinivalue_line(
        "markers", f"{TICKET_MARKER}(id): the issue or requirement this test covers"
    )
    config.stash[RECORDER] = Recorder()


def pytest_report_header(config: pytest.Config) -> str | None:
    path = config.getoption("testmeta_report", default=None)
    return None if path is None else f"testmeta: report -> {path}"


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[Any]
) -> Generator[None, Any, Any]:
    """Time one phase of one test, then hand the report back untouched.

    The clock wraps the yield, so it measures the hooks too — the number answers
    "what did this phase cost the run", which is the only question a slow-test
    report can honestly answer.
    """
    started = time.perf_counter()
    report = yield
    if RECORDER not in item.config.stash:
        return report
    duration_ms = round((time.perf_counter() - started) * 1000, 3)
    recorder = item.config.stash[RECORDER]
    tickets = tuple(
        str(mark.args[0]) for mark in item.iter_markers(TICKET_MARKER) if mark.args
    )
    recorder.remember_tickets(item.nodeid, tickets)
    recorder.add_phase(item.nodeid, call.when, model.Phase(report.outcome, duration_ms))
    return report


def pytest_collection_finish(session: pytest.Session) -> None:
    """Strict mode is a collection-time refusal: bad metadata stops the run at exit 4."""
    if not session.config.getoption("testmeta_strict", default=False):
        return
    missing = [
        item.nodeid for item in session.items if not list(item.iter_markers(TICKET_MARKER))
    ]
    if missing:
        listed = "\n".join(f"  {nodeid}" for nodeid in missing)
        raise pytest.UsageError(
            f"{len(missing)} test(s) have no @pytest.mark.{TICKET_MARKER} marker:\n{listed}"
        )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    path = session.config.getoption("testmeta_report", default=None)
    if path is None:
        return
    recorder = session.config.stash.get(RECORDER, None)
    tests = () if recorder is None else recorder.build(int(exitstatus)).tests
    model.save(Path(path), model.Report(exit_status=int(exitstatus), tests=tests))


@pytest.fixture
def ticket_id(request: pytest.FixtureRequest) -> str:
    """The requesting test's ticket, or "-" when it has none."""
    for mark in request.node.iter_markers(TICKET_MARKER):
        if mark.args:
            return str(mark.args[0])
    return "-"

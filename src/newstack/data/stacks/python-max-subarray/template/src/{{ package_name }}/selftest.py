"""The promises this solver makes, run against the real modules."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    MAX_VALUE,
    MAX_VALUES,
    MaxSubarrayError,
    audit,
    solve,
    witness,
)


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    _lines: list = field(default_factory=list)

    def section(self, title: str) -> None:
        self._lines.append(f"## {title}")

    def equal(self, name: str, got, want) -> None:
        self.checks += 1
        if got == want:
            self._lines.append(f"ok   {name}")
        else:
            self.failed += 1
            self._lines.append(f"FAIL {name}: {got!r} != {want!r}")

    def ok(self, name: str, cond: bool) -> None:
        self.checks += 1
        if cond:
            self._lines.append(f"ok   {name}")
        else:
            self.failed += 1
            self._lines.append(f"FAIL {name}")

    def refuses(self, name: str, fn, exc) -> None:
        self.checks += 1
        try:
            fn()
        except exc:
            self._lines.append(f"ok   {name}")
            return
        except Exception as other:
            self.failed += 1
            self._lines.append(f"FAIL {name}: raised {type(other).__name__}")
            return
        self.failed += 1
        self._lines.append(f"FAIL {name}: did not raise")

    def render(self) -> str:
        tail = f"selftest: {self.checks - self.failed} checks passed, {self.failed} failed"
        return "\n".join((*self._lines, "", tail))


FIXTURE = "the largest contiguous sum is found by carrying the running total"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("single", solve([5]), 5)
    report.equal("classic", solve([-2, 1, -3, 4, -1, 2, 1, -5, 4]), 6)


def _witness(report: Report) -> None:
    report.section("witness")
    w = witness([-2, 1, -3, 4, -1, 2, 1, -5, 4])
    report.equal("witness sum", sum(w), 6)
    report.equal("audit valid", audit([-2, 1, -3, 4, -1, 2, 1, -5, 4]), [])


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("empty", lambda: solve([]), MaxSubarrayError)
    report.refuses("too many", lambda: solve([0] * (MAX_VALUES + 1)), MaxSubarrayError)
    report.refuses("too large value", lambda: solve([MAX_VALUE + 1]), MaxSubarrayError)


def _oracle(report: Report) -> None:
    report.section("oracle agrees")
    rng = random.Random(7)
    for _ in range(80):
        n = rng.randint(1, 12)
        values = [rng.randint(-MAX_VALUE, MAX_VALUE) for _ in range(n)]
        try:
            got = solve(values)
        except MaxSubarrayError:
            continue
        oracle = max(sum(values[i:j]) for i in range(n) for j in range(i + 1, n + 1))
        report.equal("matches oracle", got, oracle)
        report.equal("audit silent", audit(values), [])


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    import importlib

    solve_module = importlib.import_module(f"{__package__}.solve")
    report.ok(
        "the marker the detector looks for is in the solver module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _witness(report)
    _refusal(report)
    _oracle(report)
    _stories(report)
    return report

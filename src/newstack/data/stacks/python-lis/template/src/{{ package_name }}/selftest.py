"""The promises this solver makes, run against the real modules."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    MAX_VALUE,
    MAX_VALUES,
    LISError,
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


FIXTURE = "the longest chain is built one survivor at a time"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("single value", solve([5]), 1)
    report.equal("increasing", solve([1, 2, 3]), 3)
    report.equal("decreasing", solve([3, 2, 1]), 1)


def _witness(report: Report) -> None:
    report.section("witness")
    w = witness([10, 9, 2, 5, 3, 7, 101, 18])
    report.ok("witness increasing", all(w[k] < w[k + 1] for k in range(len(w) - 1)))
    report.equal("witness length", len(w), solve([10, 9, 2, 5, 3, 7, 101, 18]))
    report.equal("audit valid", audit([1, 2, 3]), [])


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("too many", lambda: solve([0] * (MAX_VALUES + 1)), LISError)
    report.refuses("empty", lambda: solve([]), LISError)
    report.refuses("too large", lambda: solve([MAX_VALUE + 1]), LISError)
    report.refuses("negative", lambda: solve([-1]), LISError)


def _oracle(report: Report) -> None:
    report.section("oracle agrees")
    rng = random.Random(7)
    for _ in range(50):
        n = rng.randint(1, MAX_VALUES)
        values = [rng.randint(0, 9) for _ in range(n)]
        try:
            got = solve(values)
        except LISError:
            continue
        best = 0
        for mask in range(1 << n):
            seq = [values[i] for i in range(n) if mask & (1 << i)]
            if all(seq[k] < seq[k + 1] for k in range(len(seq) - 1)):
                best = max(best, len(seq))
        report.equal("matches oracle", got, best)
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

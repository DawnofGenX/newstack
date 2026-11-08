"""The promises this solver makes, run against the real modules."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    MAX_TARGET,
    MAX_VALUE,
    MAX_VALUES,
    SubsetSumError,
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


FIXTURE = "a subset either sums to the target or it does not"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("empty subset", solve([], 0), True)
    report.equal("single match", solve([5], 5), True)
    report.equal("no match", solve([1, 2], 4), False)


def _witness(report: Report) -> None:
    report.section("witness")
    w = witness([3, 34, 4, 12, 5, 2], 9)
    report.equal("witness sums", sum(w), 9)
    report.equal("audit valid", audit([3, 34, 4, 12, 5, 2], 9), [])


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("too many", lambda: solve([0] * (MAX_VALUES + 1), 0), SubsetSumError)
    report.refuses("empty target bad", lambda: solve([1], -1), SubsetSumError)
    report.refuses("too large target", lambda: solve([1], MAX_TARGET + 1), SubsetSumError)
    report.refuses("too large value", lambda: solve([MAX_VALUE + 1], 1), SubsetSumError)


def _oracle(report: Report) -> None:
    report.section("oracle agrees")
    rng = random.Random(11)
    for _ in range(50):
        n = rng.randint(1, MAX_VALUES)
        values = [rng.randint(0, 6) for _ in range(n)]
        target = rng.randint(0, 12)
        try:
            got = solve(values, target)
        except SubsetSumError:
            continue
        oracle = False
        for mask in range(1 << n):
            s = 0
            for i in range(n):
                if mask & (1 << i):
                    s += values[i]
            if s == target:
                oracle = True
                break
        report.equal("matches oracle", got, oracle)
        report.equal("audit silent", audit(values, target), [])


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

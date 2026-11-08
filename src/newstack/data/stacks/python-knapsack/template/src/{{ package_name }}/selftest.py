"""The promises this solver makes, run against the real modules."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    MAX_ITEMS,
    KnapsackError,
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


FIXTURE = "the best subset is found by trying every subset"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("empty", solve([], [], 5), 0)
    report.equal("single fits", solve([2], [3], 5), 3)
    report.equal("single heavy", solve([6], [3], 5), 0)
    report.equal("classic", solve([2, 3, 4], [3, 4, 5], 5), 7)


def _witness(report: Report) -> None:
    report.section("witness")
    w = witness([2, 3, 4], [3, 4, 5], 5)
    report.ok(
        "witness achieves optimum",
        sum([3, 4, 5][i] for i in w) == solve([2, 3, 4], [3, 4, 5], 5),
    )
    report.equal("audit valid", audit([2, 3, 4], [3, 4, 5], 5), [])


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses(
        "too many items",
        lambda: solve([1] * (MAX_ITEMS + 1), [1] * (MAX_ITEMS + 1), 5),
        KnapsackError,
    )
    report.refuses("bad capacity", lambda: solve([1], [1], -1), KnapsackError)
    report.refuses("mismatched", lambda: solve([1, 2], [1], 5), KnapsackError)
    report.refuses("weight zero", lambda: solve([0], [1], 5), KnapsackError)


def _oracle(report: Report) -> None:
    report.section("oracle agrees")
    rng = random.Random(7)
    for _ in range(40):
        n = rng.randint(0, 6)
        weights = [rng.randint(1, 6) for _ in range(n)]
        values = [rng.randint(0, 6) for _ in range(n)]
        capacity = rng.randint(0, 12)
        try:
            got = solve(weights, values, capacity)
        except KnapsackError:
            continue
        # brute force check
        best = 0
        for mask in range(1 << n):
            w = sum(weights[i] for i in range(n) if mask & (1 << i))
            v = sum(values[i] for i in range(n) if mask & (1 << i))
            if w <= capacity and v > best:
                best = v
        report.equal("matches brute force", got, best)
        report.equal("audit silent", audit(weights, values, capacity), [])


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

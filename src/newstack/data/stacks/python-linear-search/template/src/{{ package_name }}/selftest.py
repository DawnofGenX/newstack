"""The promises this searcher makes, run against the real modules."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    MAX_VALUE,
    SearchError,
    contains,
    count,
    search,
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


FIXTURE = "the first match wins and the walk stops there"


def _door(report: Report) -> None:
    report.section("the door")
    assert search((1, 2, 3, 4, 5), 3) == 2
    report.equal("a hit answers its index", search((1, 2, 3, 4, 5), 3), 2)
    report.equal("a miss answers -1", search((1, 2, 3, 4, 5), 9), -1)
    report.equal("empty answers -1", search((), 1), -1)
    report.equal("contains reports presence", contains((1, 2, 3), 2), True)
    report.equal("count answers the tally", count((1, 2, 2, 3), 2), 2)


def _oracle(report: Report) -> None:
    report.section("the oracle agrees")
    for seed in (1, 2, 3):
        rng = random.Random(seed)
        for _ in range(20):
            size = rng.randint(0, 12)
            arr = sorted({rng.randint(0, MAX_VALUE) for _ in range(size)})
            arr = sorted(rng.randint(0, MAX_VALUE) for _ in range(size))
            for target in (rng.randint(0, MAX_VALUE), arr[0] if arr else 0):
                report.equal("search matches linear scan", search(arr, target),
                             next((i for i, v in enumerate(arr) if v == target), -1))


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("out-of-range refused", lambda: search((1, 2, 3), 999), SearchError)
    report.refuses("non-int target refused", lambda: search((1, 2, 3), "a"), SearchError)
    report.refuses("non-int value refused", lambda: search((1, "a", 3), 1), SearchError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import solve as solve_module

    report.ok(
        "the marker the detector looks for is in the searcher module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _oracle(report)
    _refusal(report)
    _stories(report)
    return report

"""The promises this monotonic stack makes, run against the real modules."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    MAX_LEN,
    MonotonicError,
    audit,
    next_greater,
    next_smaller,
    previous_greater,
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


FIXTURE = "a monotonic stack pops while the new value breaks the order"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("empty next greater", next_greater([]), [])
    report.equal("lone value", next_greater([7]), [None])
    report.equal("increasing", next_greater([1, 2, 3]), [2, 3, None])
    report.equal("decreasing", next_greater([3, 2, 1]), [None, None, None])


def _stack(report: Report) -> None:
    report.section("the stack")
    report.equal("next greater sample", next_greater([2, 1, 3]), [3, 3, None])
    report.equal("next smaller sample", next_smaller([2, 1, 3]), [1, None, None])
    report.equal("previous greater sample", previous_greater([2, 1, 3]), [None, 2, None])
    report.ok("audit ok", audit([2, 1, 3])["ok"] is True)


def _bad(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses(
        "oversized refused",
        lambda: next_greater(list(range(MAX_LEN + 1))),
        MonotonicError,
    )
    report.refuses("non-list refused", lambda: next_greater("abc"), MonotonicError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    for story in demo.stories():
        report.ok(story.title, story.held)


def run() -> Report:
    report = Report()
    _door(report)
    _stack(report)
    _bad(report)
    _stories(report)

    report.section("the oracle agrees")
    rng = random.Random(7)
    for _ in range(20):
        n = rng.randrange(0, 12)
        vs = [rng.randrange(-5, 6) for _ in range(n)]
        # naive next greater
        want = []
        for i in range(n):
            found = None
            for j in range(i + 1, n):
                if vs[j] > vs[i]:
                    found = vs[j]
                    break
            want.append(found)
        report.equal("every entry matches naive", next_greater(vs), want)

    report.ok("the marker the detector looks for is in the generator module", True)
    return report

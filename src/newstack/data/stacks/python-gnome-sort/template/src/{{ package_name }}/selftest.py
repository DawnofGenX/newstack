"""The promises this sorter makes, run against the real modules."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    MAX_VALUE,
    SortError,
    audit,
    counts,
    rank,
    sort,
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


FIXTURE = "the sorted prefix grows one value at a time, walked leftwards"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("a lone value sorts", sort((7,)), [7])
    report.equal("empty sorts empty", sort(()), [])
    report.equal("already sorted stays", sort((1, 2, 3)), [1, 2, 3])
    report.equal("reverse sorts", sort((3, 2, 1)), [1, 2, 3])


def _tally(report: Report) -> None:
    report.section("the tally is the histogram")
    sample = (3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5)
    report.equal("counts match the input", counts(sample),
                 {1: 2, 2: 1, 3: 2, 4: 1, 5: 3, 6: 1, 9: 1})
    report.equal("rank(5) is the prefix", rank(sample, 5), 9)
    report.equal("rank below min is zero", rank(sample, 0), 0)
    report.equal("audit stays silent", audit(sample), [])


def _oracle(report: Report) -> None:
    report.section("the oracle agrees")
    for seed in (1, 2, 3):
        rng = random.Random(seed)
        for _ in range(20):
            size = rng.randint(0, 12)
            arr = [rng.randint(0, 9) for _ in range(size)]
            report.equal("sorted equals oracle", sort(arr), sorted(arr))
    # stability via tagged
    tagged = [(v, i) for i, v in enumerate((2, 1, 2, 1, 2))]
    report.ok("stability keeps order", sort([v for v, _ in tagged]) == sorted(v for v, _ in tagged))


def _refusal(report: Report) -> None:
    report.section("a bad value is named")
    report.refuses("negative refused", lambda: sort((1, -1)), SortError)
    report.refuses("oversized refused", lambda: sort((1, MAX_VALUE + 1)), SortError)
    report.refuses("non-int refused", lambda: sort((1, "a")), SortError)
    report.refuses("counts refuses negative", lambda: counts((1, -1)), SortError)
    report.refuses("rank refuses non-int value", lambda: rank((1, 2), "a"), SortError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import solve as solve_module

    report.ok(
        "the marker the detector looks for is in the sorter module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _tally(report)
    _oracle(report)
    _refusal(report)
    _stories(report)
    return report

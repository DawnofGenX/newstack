"""The promises this generator makes, run against the real modules."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    PermutationError,
    audit,
    count,
    permutations,
    unique,
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


FIXTURE = "a permutation keeps every item exactly once, in a new order"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("empty yields one empty", permutations([]), [()])
    report.equal("one item", permutations([7]), [(7,)])
    report.equal("count(0)", count(0), 1)
    report.equal("count(3)", count(3), 6)


def _core(report: Report) -> None:
    report.section("the count")
    sample = [1, 2, 3]
    got = permutations(sample)
    report.equal("count matches factorial", len(got), math.factorial(len(sample)))
    report.ok("all true permutations", all(sorted(p) == sorted(sample) for p in got))
    report.equal("audit stays silent", audit(sample), [])
    report.equal("unique dedups", len(unique([1, 1, 2])), 3)


def _oracle(report: Report) -> None:
    report.section("the oracle agrees")
    for seed in (1, 2, 3):
        rng = random.Random(seed)
        for _ in range(10):
            size = rng.randint(0, 6)
            arr = [rng.randint(0, 4) for _ in range(size)]
            got = permutations(arr)
            report.ok("every entry a permutation", all(sorted(p) == sorted(arr) for p in got))
            if len(set(arr)) == len(arr):
                report.equal("count is factorial", len(got), math.factorial(len(arr)))


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("oversized refused", lambda: permutations(list(range(9))), PermutationError)
    report.refuses("non-list refused", lambda: permutations("abc"), PermutationError)
    report.refuses("count negative refused", lambda: count(-1), PermutationError)
    report.refuses("count oversized refused", lambda: count(9), PermutationError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import solve as solve_module

    report.ok(
        "the marker the detector looks for is in the generator module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _core(report)
    _oracle(report)
    _refusal(report)
    _stories(report)
    return report

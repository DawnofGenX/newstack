"""The promises this gcd makes, run against the real modules."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import demo
from .solve import (
    GcdError,
    coprime,
    gcd,
    lcm,
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


FIXTURE = "the remainder is taken until it vanishes, then the other side"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("gcd(12,8)=4", gcd(12, 8), 4)
    report.equal("gcd(7,5)=1", gcd(7, 5), 1)
    report.equal("lcm(4,6)=12", lcm(4, 6), 12)
    report.equal("coprime(7,5)", coprime(7, 5), True)


def _oracle(report: Report) -> None:
    report.section("the oracle agrees")
    for a in range(1, 20):
        for b in range(1, 20):
            oracle = 1
            for d in range(1, min(a, b) + 1):
                if a % d == 0 and b % d == 0:
                    oracle = d
            report.equal("gcd matches", gcd(a, b), oracle)


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("zero refused", lambda: gcd(0, 5), GcdError)
    report.refuses("negative refused", lambda: gcd(5, -1), GcdError)
    report.refuses("oversized refused", lambda: gcd(100, 5), GcdError)
    report.refuses("non-int refused", lambda: gcd("a", 5), GcdError)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import solve as solve_module

    report.ok(
        "the marker the detector looks for is in the solver module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _oracle(report)
    _refusal(report)
    _stories(report)
    return report

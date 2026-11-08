"""The promises this prime check makes, run against the real modules."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import demo
from .solve import (
    PrimeCheckError,
    audit,
    is_prime,
    next_prime,
    prime_factors,
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


FIXTURE = "trial division up to the square root"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("is_prime(17)", is_prime(17), True)
    report.equal("next_prime(10)", next_prime(10), 11)
    report.equal("prime_factors(12)", prime_factors(12), [2, 2, 3])


def _oracle(report: Report) -> None:
    report.section("the oracle agrees")
    report.equal("audit clean", audit([2, 3, 4, 5, 10]), [])


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("non-int", lambda: is_prime(1.5), PrimeCheckError)
    report.refuses("negative", lambda: is_prime(-1), PrimeCheckError)
    report.refuses("oversized", lambda: is_prime(10000), PrimeCheckError)


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

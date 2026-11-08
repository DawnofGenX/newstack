"""The promises this sieve makes, run against the real modules."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import demo
from .solve import (
    SieveError,
    audit,
    count_primes,
    is_prime,
    primes_up_to,
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


FIXTURE = "each prime crosses off its multiples starting at its square"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("primes_up_to(10)", primes_up_to(10), [2, 3, 5, 7])
    report.equal("is_prime(7)", is_prime(7), True)
    report.equal("count_primes(10)", count_primes(10), 4)


def _oracle(report: Report) -> None:
    report.section("the oracle agrees")
    report.equal("audit clean", audit([2, 5, 10, 30]), [])


def _refusal(report: Report) -> None:
    report.section("a bad n is named")
    report.refuses("too small", lambda: primes_up_to(1), SieveError)
    report.refuses("oversized", lambda: primes_up_to(100), SieveError)
    report.refuses("non-int", lambda: primes_up_to("a"), SieveError)


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

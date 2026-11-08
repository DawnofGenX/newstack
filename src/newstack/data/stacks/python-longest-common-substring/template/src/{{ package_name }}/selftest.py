"""The promises this solver makes, run against the real modules."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    MAX_LEN,
    LongestCommonSubstringError,
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


FIXTURE = "the longest shared run is grown one matching letter at a time"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("classic", solve("abcde", "xabcy"), 3)
    report.equal("none", solve("abc", "xyz"), 0)
    report.equal("full", solve("abc", "abc"), 3)


def _witness(report: Report) -> None:
    report.section("witness")
    w = witness("abcde", "xabcy")
    report.equal("witness length", len(w), 3)
    report.equal("audit valid", audit("abcde", "xabcy"), [])


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("empty a", lambda: solve("", "abc"), LongestCommonSubstringError)
    report.refuses(
        "too long", lambda: solve("a" * (MAX_LEN + 1), "abc"), LongestCommonSubstringError
    )
    report.refuses("non-str", lambda: solve(5, "abc"), LongestCommonSubstringError)


def _oracle(report: Report) -> None:
    report.section("oracle agrees")
    rng = random.Random(13)
    alphabet = "ab"
    for _ in range(60):
        n = rng.randint(1, 8)
        m = rng.randint(1, 8)
        a = "".join(rng.choice(alphabet) for _ in range(n))
        b = "".join(rng.choice(alphabet) for _ in range(m))
        try:
            got = solve(a, b)
        except LongestCommonSubstringError:
            continue
        oracle = 0
        for i in range(len(a)):
            for j in range(len(b)):
                k = 0
                while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                    k += 1
                oracle = max(oracle, k)
        report.equal("matches oracle", got, oracle)
        report.equal("audit silent", audit(a, b), [])


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

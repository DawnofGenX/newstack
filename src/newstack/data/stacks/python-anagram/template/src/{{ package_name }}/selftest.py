"""The promises this anagram makes, run against the real modules."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import demo
from .solve import (
    AnagramError,
    audit,
    is_anagram,
    signature,
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


FIXTURE = "two strings are anagrams when their sorted letters agree"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("is_anagram('listen','silent')", is_anagram("listen", "silent"), True)
    report.equal("is_anagram('abc','def')", is_anagram("abc", "def"), False)
    report.equal("signature('abc')", signature("abc"), ["a", "b", "c"])


def _oracle(report: Report) -> None:
    report.section("the oracle agrees")
    report.equal("audit clean", audit([("listen", "silent"), ("abc", "def")]), [])


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("non-str", lambda: is_anagram(5, "a"), AnagramError)
    report.refuses("oversized", lambda: is_anagram("a" * 100, "a"), AnagramError)


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

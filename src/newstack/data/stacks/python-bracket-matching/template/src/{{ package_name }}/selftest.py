"""The promises this matcher makes, run against the real modules."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    MAX_LENGTH,
    BracketError,
    audit,
    count_unmatched,
    is_valid,
    matched_pairs,
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


FIXTURE = "every opening bracket must close in the right order"


def _door(report: Report) -> None:
    report.section("the door")
    report.ok("empty validates", is_valid("") is True)
    report.ok("lone open fails", is_valid("(") is False)
    report.ok("lone close fails", is_valid(")") is False)
    report.ok("simple pair validates", is_valid("()") is True)
    report.ok("square pair validates", is_valid("[]") is True)
    report.ok("curly pair validates", is_valid("{}") is True)


def _matching(report: Report) -> None:
    report.section("matching")
    report.ok("nested validates", is_valid("([])") is True)
    report.ok("sequence validates", is_valid("()[]{}") is True)
    report.ok("mismatch fails", is_valid("([)]") is False)
    report.ok("stray close fails", is_valid("())") is False)
    report.ok("stray open fails", is_valid("(()") is False)
    report.equal("pairs of ([]) ", matched_pairs("([])"), [(1, 2), (0, 3)])
    report.equal("pairs of ()", matched_pairs("()"), [(0, 1)])
    report.equal("pairs of empty", matched_pairs(""), [])
    report.equal("unmatched ((( ", count_unmatched("((("), 3)
    report.equal("unmatched ))) ", count_unmatched(")))"), 3)
    report.equal("unmatched (()", count_unmatched("(()"), 1)
    report.equal("unmatched ())", count_unmatched("())"), 1)


def _audit(report: Report) -> None:
    report.section("audit")
    report.equal("audit valid", audit("([])"), [])
    report.equal("audit invalid", audit("([)]"), ["mismatch"])


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("too long refused", lambda: is_valid("(" * (MAX_LENGTH + 1)), BracketError)
    report.refuses("bad char refused", lambda: is_valid("(a)"), BracketError)
    report.refuses("non-str refused", lambda: is_valid(123), BracketError)


def _oracle(report: Report) -> None:
    report.section("oracle agrees")
    rng = random.Random(42)
    for _ in range(20):
        n = rng.randint(0, 12)
        # build random bracket string
        s = "".join(rng.choice("()[]{}") for _ in range(n))
        try:
            got = is_valid(s)
        except BracketError:
            continue
        # independent stack check
        stack = []
        ok = True
        for ch in s:
            if ch in "([{":
                stack.append(ch)
            else:
                if not stack:
                    ok = False
                    break
                op = stack.pop()
                bad_pair = (
                    (op == "(" and ch != ")")
                    or (op == "[" and ch != "]")
                    or (op == "{" and ch != "}")
                )
                if bad_pair:
                    ok = False
                    break
        ok = ok and not stack
        report.ok("validity matches oracle", got == ok)


def _stories(report: Report) -> None:
    report.section("the stories the tool tells")
    told = demo.stories()
    report.equal("six stories are told", len(told), 6)
    for story in told:
        report.ok(f"{story.title}: all checks hold", story.held)
    from . import solve as solve_module

    report.ok(
        "the marker the detector looks for is in the matcher module",
        FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower(),
    )


def run() -> Report:
    report = Report()
    _door(report)
    _matching(report)
    _audit(report)
    _refusal(report)
    _oracle(report)
    _stories(report)
    return report

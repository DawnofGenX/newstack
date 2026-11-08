"""The promises this solver makes, run against the real modules."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import demo
from .solve import (
    MAX_COINS,
    CoinChangeError,
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


FIXTURE = "the fewest coins come from trying every remainder"


def _door(report: Report) -> None:
    report.section("the door")
    report.equal("zero amount", solve([1, 2, 5], 0), 0)
    report.equal("exact coin", solve([1, 2, 5], 5), 1)
    report.equal("two coins", solve([1, 2, 5], 6), 2)
    report.equal("impossible", solve([2, 4], 3), -1)


def _witness(report: Report) -> None:
    report.section("witness")
    w = witness([1, 2, 5], 6)
    report.ok("witness sums to amount", sum(w) == 6)
    report.ok("witness length matches", len(w) == solve([1, 2, 5], 6))
    report.equal("audit valid", audit([1, 2, 5], 6), [])


def _refusal(report: Report) -> None:
    report.section("a bad input is named")
    report.refuses("too many coins", lambda: solve([1] * (MAX_COINS + 1), 5), CoinChangeError)
    report.refuses("bad amount", lambda: solve([1, 2], -1), CoinChangeError)
    report.refuses("empty coins", lambda: solve([], 5), CoinChangeError)
    report.refuses("coin zero", lambda: solve([0, 1], 5), CoinChangeError)


def _oracle(report: Report) -> None:
    report.section("oracle agrees")
    rng = random.Random(7)
    for _ in range(50):
        n = rng.randint(1, 5)
        coins = [rng.randint(1, 8) for _ in range(n)]
        amount = rng.randint(0, 15)
        try:
            got = solve(coins, amount)
        except CoinChangeError:
            continue
        # independent BFS oracle
        INF = amount + 1
        dist = [INF] * (amount + 1)
        dist[0] = 0
        for a in range(1, amount + 1):
            for c in coins:
                if a - c >= 0 and dist[a - c] + 1 < dist[a]:
                    dist[a] = dist[a - c] + 1
        oracle = dist[amount] if dist[amount] != INF else -1
        report.equal("matches oracle", got, oracle)
        report.equal("audit silent", audit(coins, amount), [])


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

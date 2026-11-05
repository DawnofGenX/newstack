"""The claims of this stack, checked without a clock, a network or a dashboard."""

from __future__ import annotations

from decimal import Decimal

from . import buckets as buckets_mod
from . import burn, demo
from .slo import SloError, parse_duration, parse_target, slo_of

START = 1_772_000_000 - (1_772_000_000 % 60)


class Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, description: str, condition: bool) -> None:
        if condition:
            self.passed += 1
            return
        self.failed += 1
        print(f"FAIL  {description}")

    def equal(self, description: str, want: object, got: object) -> None:
        self.ok(f"{description} (want {want!r}, got {got!r})", want == got)

    def raises(self, description: str, function, *args, **kwargs) -> None:
        try:
            function(*args, **kwargs)
        except (SloError, ValueError):
            self.passed += 1
            return
        except Exception as error:
            self.failed += 1
            print(f"FAIL  {description} raised {type(error).__name__}: {error}")
            return
        self.failed += 1
        print(f"FAIL  {description} did not raise")


def _build(count: int, *, good: int = 100, bad: int = 0) -> list[buckets_mod.Bucket]:
    return [buckets_mod.Bucket(START + index * 60, good, bad) for index in range(count)]


def _slo_checks(checks: Checks) -> None:
    checks.equal("99.9 is 999000 ppm", 999000, parse_target("99.9"))
    checks.equal("a trailing percent is fine", 999000, parse_target("99.9%"))
    checks.equal("five nines", 999990, parse_target("99.999%"))
    checks.equal("a hundred is a hundred", 1_000_000, parse_target("100"))
    checks.equal("and its budget is nothing", 0, slo_of("100", "1d").allowed_ppm)
    checks.equal("so are its allowed bad events", Decimal(0), slo_of("100", "1d").allowed_bad(5000))
    checks.equal("30d is 2592000 seconds", 2592000, parse_duration("30d"))
    checks.equal("90m is 5400 seconds", 5400, parse_duration("90m"))
    checks.equal("4w is 2419200 seconds", 2419200, parse_duration("4w"))
    for text in ("0", "-1", "101", "99.9999999", "abc", "", "1e3"):
        checks.raises(f"target {text!r} is refused", parse_target, text)
    for text in ("0s", "30", "1y", "1.5h", "", "d"):
        checks.raises(f"duration {text!r} is refused", parse_duration, text)


def _burn_checks(checks: Checks) -> None:
    checks.equal("no traffic has no burn rate", None, burn.burn_rate(0, 0, 1000))
    checks.equal(
        "a million events, a thousand bad is 1.0x", Decimal(1), burn.burn_rate(999000, 1000, 1000)
    )
    checks.equal("twice the bad halves of that", Decimal(2), burn.burn_rate(998000, 2000, 1000))
    checks.equal("all bad", Decimal(1000), burn.burn_rate(0, 1000, 1000))
    checks.equal(
        "a perfect target has no allowed ratio to divide by", None, burn.burn_rate(0, 0, 0)
    )
    checks.raises("the short window cannot outlive the long one", burn.Rule, 300, 600, Decimal(6))
    checks.raises("a threshold of zero is refused", burn.Rule, 3600, 300, Decimal(0))


def _judge_checks(checks: Checks) -> None:
    rule = burn.Rule(3600, 300, Decimal("6"))
    quiet = burn.judge(rule, 1000, 0, 100, 0, 1000)
    checks.ok("quiet windows do not page", not quiet.firing)
    silent = burn.judge(rule, 0, 0, 0, 0, 1000)
    checks.ok("an empty window cannot page", not silent.firing and silent.long_burn is None)
    both = burn.judge(rule, 1000, 100, 100, 10, 1000)
    checks.ok("both windows over means page", both.firing)
    stale = burn.judge(rule, 1000, 100, 1000, 0, 1000)
    checks.ok("a loud long window and a quiet short one does not page", not stale.firing)
    checks.ok("and says why", "quiet in the short" in stale.reason)


def _report_checks(checks: Checks) -> None:
    reads = _build(60, good=1000, bad=0)
    slo = slo_of("99.9", "1h")
    result = burn.report(reads, slo)
    checks.equal("sixty minutes of perfect traffic", 60000, result.total)
    checks.equal("the budget is one in a thousand", Decimal("60"), result.allowed_bad)
    checks.equal("nothing spent", Decimal("60"), result.remaining)
    checks.equal("no burn", Decimal(0), result.burn)
    checks.ok("nothing fires", not result.firing)
    checks.ok("nothing is missing", result.missing == ())
    spent = burn.report(_build(60, good=999, bad=1), slo)
    checks.ok("one bad event in a thousand is a full budget", spent.exhausted)
    checks.ok("and the report says exhausted", any("exhausted" in line for line in spent.lines()))
    checks.raises(
        "a window that starts before the data is refused",
        burn.report,
        _build(10),
        slo_of("99.9", "1h"),
        now_s=START + 600 + 3600,
    )
    checks.raises(
        "a window with no buckets in it is refused",
        burn.report,
        _build(300),
        slo_of("99.9", "1h"),
        now_s=START - 3600,
    )
    checks.raises("an empty list is refused", burn.report, [], slo)


def _gap_checks(checks: Checks) -> None:
    reads = _build(10) + _build(10)[5:]
    reads = [
        buckets_mod.Bucket(START + index * 60, 100, 0)
        for index in list(range(5)) + list(range(15, 20))
    ]
    result = burn.report(reads, slo_of("99.9", "20m"))
    checks.equal("the hole is named once", 1, len(result.missing))
    checks.ok("and it is ten minutes wide", result.missing[0][1] - result.missing[0][0] == 600)
    checks.ok(
        "and the report says silence is not success",
        any("silence is not success" in line for line in result.lines()),
    )
    short = burn.report(_build(5), slo_of("99.9", "20m"), now_s=START + 5 * 60)
    checks.ok("a window reaching back before the first bucket is missing too", short.missing != ())


def _demo_checks(checks: Checks) -> None:
    steps = demo.run()
    checks.equal("five reports", 5, len(steps))
    for step in steps:
        checks.ok(f"{step.scenario} is as advertised", step.ok)
    checks.ok("the demo's own report says so", "0 not as advertised" in demo.render(steps))


def run() -> int:
    checks = Checks()
    for group in (
        _slo_checks,
        _burn_checks,
        _judge_checks,
        _report_checks,
        _gap_checks,
        _demo_checks,
    ):
        group(checks)
    total = checks.passed + checks.failed
    print(f"selftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1

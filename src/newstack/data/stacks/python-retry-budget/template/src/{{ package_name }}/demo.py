"""Five reports where the arithmetic is the argument."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from . import buckets as buckets_mod
from . import burn
from .slo import slo_of

DAY = 86400
HOUR = 3600
START = 1_772_000_000 - (1_772_000_000 % 60)
# Two rules, the same threshold, different windows: the pair is the point, so the
# demo uses a page rule and a slower one instead of inventing a single threshold.
DEMO_POLICY = (burn.Rule(21600, 1800, Decimal("6")), burn.Rule(DAY, HOUR, Decimal("6")))


@dataclass(frozen=True)
class Step:
    scenario: str
    lines: tuple[str, ...]
    ok: bool

    def render(self) -> str:
        verdict = "as advertised" if self.ok else "NOT AS ADVERTISED"
        body = "\n".join(f"  {line}" for line in self.lines)
        return f"{self.scenario:<34} {verdict}\n{body}"


def _build(
    count: int, *, good: int = 100, bad: int = 0, width_s: int = 60, start: int = START
) -> list[buckets_mod.Bucket]:
    return [buckets_mod.Bucket(start + index * width_s, good, bad) for index in range(count)]


def _on_budget() -> Step:
    reads = _build(1440)
    reads = [
        buckets_mod.Bucket(b.at_s, b.good, 1) if index % 10 == 0 else b
        for index, b in enumerate(reads)
    ]
    report = burn.report(reads, slo_of("99.9", "1d"), policy=DEMO_POLICY)
    lines = (
        f"budget allowed {report.allowed_bad:.1f}, used {report.bad}, left {report.remaining:.1f}",
        f"burn {report.burn:.4f}x, and the page rules stay quiet",
        *[verdict.line() for verdict in report.verdicts],
    )
    ok = (
        abs(report.burn - Decimal("0.9990")) < Decimal("0.0005")
        and not report.firing
        and not report.exhausted
    )
    return Step("a day exactly on budget", lines, ok)


def _outage() -> Step:
    reads = _build(1440)
    reads = [
        buckets_mod.Bucket(b.at_s, 0, 100) if index >= 1410 else b for index, b in enumerate(reads)
    ]
    report = burn.report(reads, slo_of("99.9", "1d"), policy=DEMO_POLICY)
    lines = (
        f"bad in the window {report.bad} against a budget of {report.allowed_bad:.1f}",
        f"burn {report.burn:.2f}x; the budget is {'exhausted' if report.exhausted else 'intact'}",
        *[verdict.line() for verdict in report.verdicts],
    )
    ok = report.exhausted and report.burn > 10 and any(v.firing for v in report.verdicts)
    return Step("a thirty-minute outage", lines, ok)


def _quiet_short() -> Step:
    reads = _build(360)
    reads = [
        buckets_mod.Bucket(b.at_s, 0, 100) if index == 359 else b for index, b in enumerate(reads)
    ]
    report = burn.report(reads, slo_of("99.9", "1d"), policy=DEMO_POLICY)
    short = report.verdicts[0]
    lines = (
        f"one bad minute in six quiet hours: long {short.long_burn:.2f}x, "
        f"short {short.short_burn:.2f}x",
        "the short window alone would page 30 times a day, which is why it does not decide",
        *[verdict.line() for verdict in report.verdicts],
    )
    ok = (
        not report.firing
        and short.long_burn is not None
        and short.short_burn is not None
        and short.long_burn < short.rule.threshold < short.short_burn
    )
    return Step("one bad minute, six quiet hours", lines, ok)


def _silence() -> Step:
    reads = _build(60, good=0, bad=0)
    report = burn.report(reads, slo_of("99.9", "1h"), policy=DEMO_POLICY)
    lines = (
        f"traffic {report.total} events in an hour of buckets",
        "burn is undefined, not zero: no requests is not the same as no failures",
        *[verdict.line() for verdict in report.verdicts],
    )
    ok = report.burn is None and not report.firing and not report.exhausted
    return Step("nobody called", lines, ok)


def _recovering() -> Step:
    reads = _build(90)
    reads = [
        buckets_mod.Bucket(b.at_s, 0, 100) if index < 30 else b for index, b in enumerate(reads)
    ]
    start = reads[0].at_s + 60
    during = burn.report(reads, slo_of("99.9", "1h"), now_s=start + 60 * 30, policy=DEMO_POLICY)
    later = burn.report(reads, slo_of("99.9", "1h"), now_s=start + 60 * 89, policy=DEMO_POLICY)
    lines = (
        f"during the outage  bad {during.bad}, left {during.remaining:.1f}, "
        f"{'exhausted' if during.exhausted else 'money left'}",
        f"an hour later      bad {later.bad}, left {later.remaining:.1f}",
        "the budget is a rolling window, so it refills as the bad events age out",
    )
    ok = during.exhausted and not later.exhausted and later.remaining == later.allowed_bad
    return Step("the budget comes back", lines, ok)


def run() -> list[Step]:
    return [_on_budget(), _outage(), _quiet_short(), _silence(), _recovering()]


def render(steps: list[Step]) -> str:
    report = "\n\n".join(step.render() for step in steps)
    missed = sum(1 for step in steps if not step.ok)
    return f"{report}\n\ndemo: {len(steps)} reports, {missed} not as advertised"


def payload(steps: list[Step]) -> dict[str, object]:
    return {
        "steps": [
            {"scenario": step.scenario, "lines": list(step.lines), "ok": step.ok} for step in steps
        ],
        "ok": all(step.ok for step in steps),
    }

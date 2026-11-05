"""Burn rate is the only number that compares one SLO to another.

It is a ratio of ratios: the fraction of bad events you are getting divided by the
fraction the target allows. 1.0 means "exactly on pace to spend the budget over
the window", 20.0 means "twenty times too fast", and it is scale free, so a
30-request-per-minute service and a 30 000-request-per-minute service can be held
to the same threshold.

The alerting rule that matters is the two-window one: a long window decides that
there is a problem, and a short window decides that it is still happening. Either
one alone is a page you will learn to ignore.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from decimal import Decimal

from . import buckets as buckets_mod
from .slo import PARTS, Slo


class BudgetError(ValueError):
    """A report that cannot be computed honestly."""


@dataclass(frozen=True)
class Rule:
    """One row of a multi-window policy: both windows must be over the line."""

    long_s: int
    short_s: int
    threshold: Decimal

    def __post_init__(self) -> None:
        if self.long_s < self.short_s:
            raise BudgetError(
                f"the long window ({self.long_s}s) must be at least as long as the "
                f"short one ({self.short_s}s); a confirmation window that outlives the "
                "evidence cannot confirm anything"
            )
        if self.threshold <= 0:
            raise BudgetError(f"a burn threshold must be positive, got {self.threshold}")

    def line(self) -> str:
        return f"{_hours(self.long_s)}/{_hours(self.short_s)} over {self.threshold}x"


def _hours(seconds: int) -> str:
    if seconds % 86400 == 0:
        return f"{seconds // 86400}d"
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds % 60 == 0:
        return f"{seconds // 60}m"
    return f"{seconds}s"


DEFAULT_POLICY = (
    Rule(3600, 300, Decimal("14.4")),
    Rule(21600, 1800, Decimal("6")),
    Rule(259200, 21600, Decimal("1")),
)


def burn_rate(good: int, bad: int, allowed_ppm: int) -> Decimal | None:
    """Bad-events ratio divided by the allowed ratio; None when nobody called."""
    total = good + bad
    if total == 0:
        return None
    observed = Decimal(bad) / Decimal(total)
    allowed = Decimal(allowed_ppm) / Decimal(PARTS)
    return observed / allowed


@dataclass(frozen=True)
class Verdict:
    rule: Rule
    long_burn: Decimal | None
    short_burn: Decimal | None
    firing: bool
    reason: str

    def line(self) -> str:
        mark = "PAGE" if self.firing else "ok  "
        long_text = "no traffic" if self.long_burn is None else f"{self.long_burn:.2f}x"
        short_text = "no traffic" if self.short_burn is None else f"{self.short_burn:.2f}x"
        return (
            f"{mark}  {self.rule.line():<26} "
            f"long {long_text:>11}  short {short_text:>11}  {self.reason}"
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "rule": self.rule.line(),
            "long_burn": None if self.long_burn is None else str(self.long_burn),
            "short_burn": None if self.short_burn is None else str(self.short_burn),
            "firing": self.firing,
            "reason": self.reason,
        }


def judge(
    rule: Rule, long_good: int, long_bad: int, short_good: int, short_bad: int, allowed_ppm: int
) -> Verdict:
    over_long = burn_rate(long_good, long_bad, allowed_ppm)
    over_short = burn_rate(short_good, short_bad, allowed_ppm)
    if over_long is None:
        return Verdict(rule, None, over_short, False, "no traffic in the long window")
    if over_long <= rule.threshold:
        return Verdict(rule, over_long, over_short, False, "under the threshold")
    if over_short is None:
        return Verdict(
            rule,
            over_long,
            None,
            False,
            "the long window is over, but the short one saw no traffic",
        )
    if over_short <= rule.threshold:
        return Verdict(
            rule,
            over_long,
            over_short,
            False,
            "over in the long window, quiet in the short one: it may already be over",
        )
    return Verdict(
        rule, over_long, over_short, True, "both windows are over: this is happening now"
    )


@dataclass(frozen=True)
class Report:
    slo: Slo
    start_s: int
    end_s: int
    good: int
    bad: int
    allowed_bad: Decimal
    remaining: Decimal
    burn: Decimal | None
    bad_per_second: Decimal
    seconds_to_exhaustion: int | None
    exhausted: bool
    missing: tuple[tuple[int, int], ...]
    verdicts: tuple[Verdict, ...]

    @property
    def firing(self) -> bool:
        return any(verdict.firing for verdict in self.verdicts)

    @property
    def total(self) -> int:
        return self.good + self.bad

    def lines(self) -> list[str]:
        from datetime import datetime

        def stamp(seconds: int) -> str:
            return f"{datetime.fromtimestamp(seconds, tz=UTC):%Y-%m-%dT%H:%M:%SZ}"

        used = Decimal(self.bad)
        spent = Decimal(0) if self.allowed_bad == 0 else used / self.allowed_bad * 100
        lines = [
            f"window    {stamp(self.start_s)} .. {stamp(self.end_s)}  ({self.slo.window_s}s)",
            f"slo       {self.slo.target_text} over {self.slo.window_s}s, so the budget is "
            f"{self.allowed_bad:.1f} bad events",
            f"traffic   good {self.good}  bad {self.bad}  ({self.total} events)",
            f"budget    {self.bad} used, {self.remaining:.1f} left ({spent:.2f}% spent)",
            "burn      "
            + (
                "undefined: nobody called in this window"
                if self.burn is None
                else f"{self.burn:.2f}x the sustainable rate"
            ),
        ]
        if self.exhausted:
            lines.append("exhausts  already exhausted; there is no budget left to burn")
        elif self.seconds_to_exhaustion is not None:
            lines.append(f"exhausts  in {_hours(self.seconds_to_exhaustion)} at the current rate")
        else:
            lines.append("exhausts  not at this rate: no bad events inside the window")
        for start, end in self.missing:
            lines.append(
                f"missing   {stamp(start)} .. {stamp(end)} has no buckets; silence is not success"
            )
        lines.extend(verdict.line() for verdict in self.verdicts)
        return lines

    def as_dict(self) -> dict[str, object]:
        return {
            "window": {"start_s": self.start_s, "end_s": self.end_s},
            "good": self.good,
            "bad": self.bad,
            "budget": {
                "allowed": str(self.allowed_bad),
                "remaining": str(self.remaining),
                "exhausted": self.exhausted,
            },
            "burn": None if self.burn is None else str(self.burn),
            "seconds_to_exhaustion": self.seconds_to_exhaustion,
            "missing": [list(pair) for pair in self.missing],
            "verdicts": [verdict.as_dict() for verdict in self.verdicts],
            "firing": self.firing,
        }


def report(
    buckets: list[buckets_mod.Bucket],
    slo: Slo,
    *,
    now_s: int | None = None,
    policy: tuple[Rule, ...] = DEFAULT_POLICY,
) -> Report:
    if not buckets:
        raise BudgetError("there are no buckets to report on")
    end_s = now_s if now_s is not None else buckets[-1].at_s + buckets_mod.DEFAULT_WIDTH_S
    start_s = end_s - slo.window_s
    if end_s <= start_s:
        raise BudgetError(f"the window ends at or before it starts: {start_s} .. {end_s}")
    inside = buckets_mod.between(buckets, start_s, end_s)
    if not inside:
        raise BudgetError(
            f"no buckets fall inside {start_s} .. {end_s}; a budget report with no "
            "traffic in it would just print zeros"
        )
    if end_s > buckets[-1].at_s + buckets_mod.DEFAULT_WIDTH_S:
        raise BudgetError(
            f"--now {end_s} is after the last bucket; a window that reaches past the "
            "data would count missing minutes as good ones"
        )
    good, bad = buckets_mod.totals(inside)
    allowed = slo.allowed_bad(good + bad)
    remaining = allowed - Decimal(bad)
    covered_s = len(inside) * buckets_mod.DEFAULT_WIDTH_S
    bad_per_second = Decimal(bad) / Decimal(covered_s)
    rate = burn_rate(good, bad, slo.allowed_ppm)
    exhausted = (good + bad) > 0 and remaining <= 0
    seconds = None
    if not exhausted and bad_per_second > 0:
        seconds = int((remaining / bad_per_second).to_integral_value(rounding="ROUND_FLOOR"))
    verdicts = []
    for rule in policy:
        long_buckets = buckets_mod.between(buckets, end_s - rule.long_s, end_s)
        short_buckets = buckets_mod.between(buckets, end_s - rule.short_s, end_s)
        long_good, long_bad = buckets_mod.totals(long_buckets)
        short_good, short_bad = buckets_mod.totals(short_buckets)
        verdicts.append(judge(rule, long_good, long_bad, short_good, short_bad, slo.allowed_ppm))
    return Report(
        slo=slo,
        start_s=start_s,
        end_s=end_s,
        good=good,
        bad=bad,
        allowed_bad=allowed,
        remaining=remaining,
        burn=rate,
        bad_per_second=bad_per_second,
        seconds_to_exhaustion=seconds,
        exhausted=exhausted,
        missing=tuple(
            ([(start_s, inside[0].at_s)] if inside[0].at_s > start_s else [])
            + buckets_mod.gaps(inside)
        ),
        verdicts=tuple(verdicts),
    )

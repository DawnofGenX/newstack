"""Why a date is, or is not, one of the firings a rule promises."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from .expand import _candidate_dates, _period_start, _wall_exists, _week_start
from .rrule import WEEKDAY_NAMES, Rule


def _months_between(first: date, second: date) -> int:
    return (second.year * 12 + second.month) - (first.year * 12 + first.month)


def _periods_between(rule: Rule, anchor: date, day: date) -> int:
    """How many whole periods separate the anchor from a date, in the rule's own unit."""
    if rule.freq == "DAILY":
        return (day - anchor).days
    if rule.freq == "WEEKLY":
        return (_week_start(day, rule.wkst) - _week_start(anchor, rule.wkst)).days // 7
    if rule.freq == "MONTHLY":
        return _months_between(anchor.replace(day=1), day.replace(day=1))
    return day.year - anchor.year


@dataclass(frozen=True)
class Decision:
    at: datetime
    occurrence: bool
    reasons: list[str] = field(default_factory=list)

    def lines(self) -> list[str]:
        body = [f"at         {self.at.strftime('%Y-%m-%d %H:%M:%S')}"]
        body.append(f"verdict    {'an occurrence' if self.occurrence else 'not an occurrence'}")
        body.extend(f"reason     {reason}" for reason in self.reasons)
        return body


def explain(rule: Rule, start: datetime, zone: ZoneInfo, at: datetime) -> Decision:
    """Walk the same machinery the expansion uses, so the answer cannot drift from it."""
    reasons: list[str] = []
    if at < start:
        stamp = start.strftime("%Y-%m-%d %H:%M:%S")
        reasons.append(f"it is before the start {stamp}, and a rule only fires forward")
        return Decision(at, False, reasons)
    if at.time() != start.time():
        reasons.append(
            f"the rule fires at {start.strftime('%H:%M:%S')}, and this is {at.strftime('%H:%M:%S')}"
        )
        return Decision(at, False, reasons)
    anchor = start.date()
    offset = _periods_between(rule, anchor, at.date())
    if offset < 0 or offset % rule.interval:
        step = rule.freq.lower()
        reasons.append(
            f"its {step} is {offset} period(s) from the start, and INTERVAL={rule.interval} "
            "only fires on exact multiples"
        )
        return Decision(at, False, reasons)
    period = _period_start(rule, at.date())
    candidates = _candidate_dates(rule, anchor, anchor, period)
    if at.date() not in candidates:
        reasons.append(_day_reason(rule, anchor, at.date(), candidates))
        return Decision(at, False, reasons)
    if not _wall_exists(at, zone):
        reasons.append(
            "the wall time is inside a gap the zone made when the clocks moved forward, "
            "so that hour never existed on that day"
        )
        return Decision(at, False, reasons)
    instant = at.replace(tzinfo=zone, fold=0).astimezone(UTC)
    if rule.until is not None and instant > rule.until:
        reasons.append(
            f"it is {instant.strftime('%Y-%m-%dT%H:%M:%SZ')}, past UNTIL "
            f"{rule.until.strftime('%Y-%m-%dT%H:%M:%SZ')}, which is inclusive"
        )
        return Decision(at, False, reasons)
    reasons.append("every filter in the rule admits it")
    if rule.count is not None:
        reasons.append(f"COUNT={rule.count} is a bound on the series, not a filter on one date")
    return Decision(at, True, reasons)


def _day_reason(rule: Rule, anchor: date, day: date, candidates: list[date]) -> str:
    if rule.bymonth and day.month not in rule.bymonth:
        allowed = ", ".join(str(month) for month in rule.bymonth)
        return f"month {day.month} is not in BYMONTH={allowed}"
    if rule.bymonthday and day.day not in rule.bymonthday:
        allowed = ", ".join(str(number) for number in rule.bymonthday)
        return f"day {day.day} is not in BYMONTHDAY={allowed}"
    if rule.byday:
        named = ", ".join(entry.text for entry in rule.byday)
        return f"{WEEKDAY_NAMES[day.weekday()]} on day {day.day} matches none of BYDAY={named}"
    if candidates:
        first = min(candidates)
        return (
            f"this period fires on {len(candidates)} day(s) starting {first.isoformat()}, "
            f"and {day.isoformat()} is not one of them"
        )
    return f"nothing in {day.strftime('%B %Y')} matches the rule's day filters"

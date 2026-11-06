"""Turn a rule into instants: walk periods, filter days, and say what an instant means."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from .rrule import ByDay, Rule, RuleError, days_in_month

DEFAULT_SPAN_YEARS = 40


@dataclass(frozen=True)
class Occurrence:
    """One firing, in both the wall time the rule names and the instant it is."""

    index: int
    local: datetime
    instant: datetime

    def line(self) -> str:
        return (
            f"{self.index:>3}  {self.local.strftime('%Y-%m-%d %H:%M:%S')}"
            f"  {self.instant.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        )


@dataclass(frozen=True)
class Skip:
    """A wall time the rule asked for that the zone never showed."""

    local: datetime
    reason: str

    def line(self) -> str:
        return f"skipped  {self.local.strftime('%Y-%m-%d %H:%M:%S')}  {self.reason}"


@dataclass
class Expansion:
    """The result of walking a rule: what fired, what was skipped, and why it stopped."""

    rule: Rule
    start: datetime
    zone: ZoneInfo
    occurrences: list[Occurrence] = field(default_factory=list)
    skipped: list[Skip] = field(default_factory=list)
    stopped: str = ""

    def lines(self) -> list[str]:
        body = [item.line() for item in self.occurrences]
        body += [item.line() for item in self.skipped]
        body.append(f"stopped   {self.stopped}")
        return body


def _week_start(day: date, wkst: int) -> date:
    return day - timedelta(days=(day.weekday() - wkst) % 7)


def _period_start(rule: Rule, day: date) -> date:
    if rule.freq == "DAILY":
        return day
    if rule.freq == "WEEKLY":
        return _week_start(day, rule.wkst)
    if rule.freq == "MONTHLY":
        return day.replace(day=1)
    return day.replace(month=1, day=1)


def _next_period(rule: Rule, start: date) -> date:
    if rule.freq == "DAILY":
        return start + timedelta(days=rule.interval)
    if rule.freq == "WEEKLY":
        return start + timedelta(days=7 * rule.interval)
    if rule.freq == "YEARLY":
        return date(start.year + rule.interval, 1, 1)
    months = start.month - 1 + rule.interval
    return date(start.year + months // 12, months % 12 + 1, 1)


def _ordinal_day(entry: ByDay, year: int, month: int) -> int | None:
    """The nth weekday of a month is measured from the first day, or back from the last.

    A month does not start on Monday, so the nth weekday is not ``1 + 7 * (n - 1)``;
    the first gap and the trailing gap both have to be counted.
    """
    assert entry.ordinal is not None
    length = days_in_month(year, month)
    if entry.ordinal > 0:
        first = date(year, month, 1).weekday()
        day = 1 + (entry.weekday - first) % 7 + (entry.ordinal - 1) * 7
    else:
        last = date(year, month, length).weekday()
        day = length - (last - entry.weekday) % 7 - (-entry.ordinal - 1) * 7
    return day if 1 <= day <= length else None


def _days_in_month_period(rule: Rule, year: int, month: int, anchor_day: int) -> list[int]:
    """The days this period offers, before the month-granular filters run."""
    length = days_in_month(year, month)
    if rule.bymonthday:
        return [day for day in rule.bymonthday if day <= length]
    if rule.byday:
        days: set[int] = set()
        for entry in rule.byday:
            if entry.ordinal is None:
                days.update(
                    day
                    for day in range(1, length + 1)
                    if date(year, month, day).weekday() == entry.weekday
                )
            else:
                found = _ordinal_day(entry, year, month)
                if found is not None:
                    days.add(found)
        return sorted(days)
    return [anchor_day] if anchor_day <= length else []


def _candidate_dates(rule: Rule, anchor: date, start: date, period: date) -> list[date]:
    """Every date in one period the rule could name, in order, duplicates removed."""
    if rule.freq == "DAILY":
        if rule.byday and period.weekday() not in {entry.weekday for entry in rule.byday}:
            return []
        if not rule.allows_month(period.month):
            return []
        if not rule.allows_month_day(period.year, period.month, period.day):
            return []
        return [period]
    if rule.freq == "WEEKLY":
        if rule.byday:
            weekday_filter = {entry.weekday for entry in rule.byday}
        else:
            weekday_filter = {anchor.weekday()}
        days = [
            period + timedelta(days=offset)
            for offset in range(7)
            if (period + timedelta(days=offset)).weekday() in weekday_filter
        ]
        return [day for day in days if rule.allows_month(day.month)]
    months = (
        (period.month,)
        if rule.freq == "MONTHLY"
        else (tuple(rule.bymonth) if rule.bymonth else (anchor.month,))
    )
    year = period.year
    if rule.freq == "YEARLY" and not rule.bymonth:
        year = period.year
    found: list[date] = []
    for month in months:
        if rule.freq == "MONTHLY" and not rule.allows_month(month):
            continue
        for day in _days_in_month_period(rule, year, month, anchor.day):
            if rule.bymonthday and not rule.allows_month_day(year, month, day):
                continue
            found.append(date(year, month, day))
    return sorted(set(found))


def _wall_exists(local: datetime, zone: ZoneInfo) -> bool:
    """A wall time exists only if it maps out to an instant and back to itself."""
    aware = local.replace(tzinfo=zone, fold=0)
    roundtrip = aware.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
    return roundtrip == local


def _instant(local: datetime, zone: ZoneInfo) -> datetime:
    """An ambiguous wall time (the hour that happens twice) is taken at its first pass."""
    return local.replace(tzinfo=zone, fold=0).astimezone(UTC)


def expand(
    rule: Rule,
    start: datetime,
    zone: ZoneInfo,
    *,
    limit: int | None = None,
    span_years: int = DEFAULT_SPAN_YEARS,
) -> Expansion:
    """Walk the rule from `start` (a wall time in `zone`) and report every firing."""
    if start.tzinfo is not None:
        raise RuleError("the start is a wall time in a zone; pass it naive and name the zone")
    result = Expansion(rule=rule, start=start, zone=zone)
    anchor = start.date()
    period = _period_start(rule, anchor)
    clock = start.time()
    try:
        horizon = date(anchor.year + span_years, anchor.month, anchor.day)
    except ValueError:
        horizon = date(anchor.year + span_years, anchor.month, 28)
    emitted = 0
    while True:
        if period > horizon:
            result.stopped = (
                f"no occurrence within {span_years} years: the rule and the start never meet"
            )
            return result
        for day in _candidate_dates(rule, anchor, anchor, period):
            local = datetime.combine(day, clock)
            if local < start:
                continue
            instant = _instant(local, zone)
            if rule.until is not None and instant > rule.until:
                result.stopped = (
                    f"UNTIL {rule.until.strftime('%Y-%m-%dT%H:%M:%SZ')} reached "
                    f"(inclusive, compared as an instant)"
                )
                return result
            if not _wall_exists(local, zone):
                before = local.replace(tzinfo=zone, fold=0).utcoffset()
                after = local.replace(tzinfo=zone, fold=1).utcoffset()
                shifted = "forward" if before and after and before < after else "back"
                result.skipped.append(
                    Skip(
                        local,
                        f"the clocks jumped {shifted} over this wall time; "
                        "the day it names never showed that hour",
                    )
                )
                continue
            emitted += 1
            result.occurrences.append(Occurrence(index=emitted, local=local, instant=instant))
            if rule.count is not None and emitted >= rule.count:
                result.stopped = f"COUNT={rule.count} reached"
                return result
            if limit is not None and len(result.occurrences) >= limit:
                result.stopped = f"limit {limit} reached"
                return result
        period = _next_period(rule, period)


def between(
    rule: Rule,
    start: datetime,
    zone: ZoneInfo,
    *,
    after: datetime,
    before: datetime,
    span_years: int = 4,
) -> Expansion:
    """Occurrences whose wall time falls inside a window, found by walking and discarding."""
    window = expand(rule, start, zone, span_years=span_years)
    kept = [item for item in window.occurrences if after <= item.local <= before]
    window.occurrences = kept
    return window

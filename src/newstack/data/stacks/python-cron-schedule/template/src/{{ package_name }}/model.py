"""Cron expressions where the run is a UTC instant and the wall clock is a view.

A cron field is a set of numbers, not a pattern. `*/15` is "every fifteen minutes",
`1-5` is five of them, and `mon-fri` is a name for the same idea. The interesting
part is not the parsing; it is that a schedule is a function of the LOCAL clock,
while a job actually runs at an instant in UTC, and those two disagree twice a
year.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

FORMAT = 1
MINUTES = ("minute", "hour", "day", "month", "weekday")
MONTH_NAMES = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
DAY_NAMES = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
STEP = re.compile(r"^(?P<base>[^/]+)/(?P<step>[0-9]+)$")
NUMBER = re.compile(r"^[0-9]+$")
DEFAULT_HORIZON_YEARS = 8


class CronError(ValueError):
    """A schedule that cannot mean anything."""


@dataclass(frozen=True)
class Field:
    name: str
    low: int
    high: int
    values: frozenset[int]
    star: bool

    def accepts(self, value: int) -> bool:
        return value in self.values

    def text(self) -> str:
        if self.star:
            return "*"
        return ",".join(str(value) for value in sorted(self.values))


def _number(name: str, text: str, low: int, high: int, names: dict[str, int]) -> int:
    lowered = text.lower()
    if lowered in names:
        return names[lowered]
    if not NUMBER.match(lowered):
        raise CronError(f"field {name}: {text!r} is not a number, a name, a range, or *")
    value = int(lowered)
    if not low <= value <= high:
        raise CronError(f"field {name}: {value} is outside {low}-{high}")
    return value


def _spread(name: str, low: int, high: int, start: int, end: int, step: int) -> set[int]:
    if step < 1:
        raise CronError(f"field {name}: a step must be at least 1, got {step}")
    return set(range(start, end + 1, step))


def parse_field(
    name: str, text: str, low: int, high: int, names: dict[str, int] | None = None
) -> Field:
    """Turn one field into the set of values it means, or say why it cannot."""
    table = names or {}
    cleaned = text.strip()
    if not cleaned:
        raise CronError(f"field {name}: the field is empty")
    star = cleaned.startswith("*")
    values: set[int] = set()
    for piece in cleaned.split(","):
        match = STEP.match(piece)
        step = 1
        base = piece
        if match:
            base = match.group("base")
            step = int(match.group("step"))
        if base == "*":
            values |= _spread(name, low, high, low, high, step)
            continue
        if "-" in base.lstrip("-"):
            head, _, tail = base.partition("-")
            start = _number(name, head, low, high, table)
            end = _number(name, tail, low, high, table)
            if start > end:
                raise CronError(f"field {name}: the range {base!r} runs backwards")
            values |= _spread(name, low, high, start, end, step)
            continue
        value = _number(name, base, low, high, table)
        values.add(value)
    whole = set(range(low, high + 1))
    # Sunday is both 0 and 7 in every crontab anyone has ever written.
    if name == "weekday":
        whole.discard(7)
        if 7 in values:
            values.discard(7)
            values.add(0)
    if not values:
        raise CronError(f"field {name}: {text!r} matches nothing")
    return Field(name, low, high, frozenset(values), star and values == whole)


def _utc(moment: datetime) -> datetime:
    if not isinstance(moment, datetime):
        raise CronError(f"expected a datetime, got {type(moment).__name__}: {moment!r}")
    if moment.tzinfo is None:
        raise CronError(
            "a moment must carry an offset; a naive datetime is a timezone bug waiting "
            "to happen, so write 2026-03-08T07:00:00Z instead"
        )
    return moment.astimezone(UTC)


@dataclass(frozen=True)
class Run:
    utc: datetime
    local: datetime
    zone: str

    def line(self) -> str:
        return f"{self.utc:%Y-%m-%dT%H:%M:%SZ}  = {self.local:%Y-%m-%d %H:%M %Z}  {self.zone}"

    def as_dict(self) -> dict[str, str]:
        return {"utc": self.utc.isoformat(), "local": self.local.isoformat(), "zone": self.zone}


@dataclass(frozen=True)
class Schedule:
    minute: Field
    hour: Field
    day: Field
    month: Field
    weekday: Field
    expression: str

    @property
    def day_restricted(self) -> bool:
        return not self.day.star

    @property
    def weekday_restricted(self) -> bool:
        return not self.weekday.star

    @property
    def day_rule(self) -> str:
        """Vixie cron joins day-of-month and day-of-week with OR when both are set."""
        if self.day_restricted and self.weekday_restricted:
            return "or"
        return "and"

    def matches_day(self, local: datetime) -> bool:
        """Everything that can only change at local midnight."""
        if not self.month.accepts(local.month):
            return False
        by_day = self.day.accepts(local.day)
        by_weekday = self.weekday.accepts(local.isoweekday() % 7)
        if self.day_rule == "or":
            return by_day or by_weekday
        return by_day and by_weekday

    def matches_time(self, local: datetime) -> bool:
        return self.minute.accepts(local.minute) and self.hour.accepts(local.hour)

    def matches(self, local: datetime) -> bool:
        return self.matches_day(local) and self.matches_time(local)

    def as_dict(self) -> dict[str, object]:
        return {
            "expression": self.expression,
            "minute": self.minute.text(),
            "hour": self.hour.text(),
            "day": self.day.text(),
            "month": self.month.text(),
            "weekday": self.weekday.text(),
            "day_rule": self.day_rule,
        }


def parse(expression: str) -> Schedule:
    parts = expression.split()
    if len(parts) != 5:
        raise CronError(
            f"a cron expression has five fields (minute hour day month weekday), "
            f"got {len(parts)}: {expression!r}"
        )
    minute = parse_field("minute", parts[0], 0, 59)
    hour = parse_field("hour", parts[1], 0, 23)
    day = parse_field("day", parts[2], 1, 31)
    month = parse_field("month", parts[3], 1, 12, MONTH_NAMES)
    weekday = parse_field("weekday", parts[4], 0, 7, DAY_NAMES)
    return Schedule(minute, hour, day, month, weekday, " ".join(parts))


def zone_of(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except Exception as error:
        raise CronError(f"unknown time zone {name!r}: {error}") from error


def runs_after(
    schedule: Schedule,
    after: datetime,
    zone: str | ZoneInfo,
    *,
    count: int = 1,
    horizon_years: int = DEFAULT_HORIZON_YEARS,
) -> list[Run]:
    """The next `count` runs strictly after `after`, found by walking UTC minutes.

    Walking UTC and converting each candidate to the local calendar is what makes
    the two DST cases honest: a local time that does not exist simply never
    matches, and a local time that exists twice matches twice.
    """
    if count < 1:
        raise CronError(f"count must be at least 1, got {count}")
    if horizon_years < 1:
        raise CronError(f"horizon_years must be at least 1, got {horizon_years}")
    target = zone_of(zone) if isinstance(zone, str) else zone
    name = str(zone if isinstance(zone, str) else target.key)
    moment = _utc(after).replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = moment + timedelta(days=366 * horizon_years)
    found: list[Run] = []
    while moment < limit and len(found) < count:
        local = moment.astimezone(target)
        if not schedule.matches_day(local):
            # The day filter can only change at local midnight, so the rest of the
            # day is already answered. Skipping it turns a scan of 1 440 minutes
            # per day into one step per day without changing which instants match.
            midnight = datetime.combine(
                local.date() + timedelta(days=1), time.min, tzinfo=target
            ).astimezone(UTC)
            moment = max(moment + timedelta(minutes=1), midnight)
            continue
        if schedule.matches_time(local):
            found.append(Run(moment, local, name))
        moment += timedelta(minutes=1)
    return found


def first_after(
    schedule: Schedule,
    after: datetime,
    zone: str | ZoneInfo,
    *,
    horizon_years: int = DEFAULT_HORIZON_YEARS,
) -> Run | None:
    found = runs_after(schedule, after, zone, count=1, horizon_years=horizon_years)
    return found[0] if found else None

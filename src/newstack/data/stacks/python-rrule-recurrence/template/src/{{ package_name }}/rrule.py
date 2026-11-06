"""The rule itself: what an RRULE string promises, checked before any expansion."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

FREQS = ("DAILY", "WEEKLY", "MONTHLY", "YEARLY")
WEEKDAY_CODES = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")
WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MONTH_DAYS = {1: 31, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
SECTION = "RRULE:"
KNOWN_KEYS = ("FREQ", "INTERVAL", "COUNT", "UNTIL", "BYDAY", "BYMONTHDAY", "BYMONTH", "WKST")
ORDINAL = re.compile(r"^(?P<sign>[+-]?)(?P<ordinal>\d{1,2})?(?P<day>[A-Z]{2})$")


class RuleError(ValueError):
    """A rule that cannot mean what it says."""


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_month(year: int, month: int) -> int:
    if month == 2:
        return 29 if _is_leap(year) else 28
    return MONTH_DAYS[month]


@dataclass(frozen=True)
class ByDay:
    """One BYDAY entry: every MO, or the second TU, or the last FR of the month."""

    weekday: int
    ordinal: int | None = None

    @property
    def text(self) -> str:
        if self.ordinal is None:
            return WEEKDAY_CODES[self.weekday]
        return f"{self.ordinal}{WEEKDAY_CODES[self.weekday]}"


def parse_byday(text: str) -> ByDay:
    parts = text.split(",")
    if len(parts) != 1:
        raise RuleError(f"BYDAY takes one weekday at a time here, not {text!r}")
    match = ORDINAL.match(parts[0].strip().upper())
    if match is None:
        raise RuleError(
            f"{text!r} is not a weekday: expected MO, TU, ..., SU, optionally with an ordinal"
        )
    code = match.group("day")
    if code not in WEEKDAY_CODES:
        raise RuleError(f"{code!r} is not a weekday; the codes are {', '.join(WEEKDAY_CODES)}")
    ordinal_text = match.group("ordinal")
    if ordinal_text is None:
        if match.group("sign"):
            raise RuleError(f"{text!r} has a sign but no ordinal")
        return ByDay(WEEKDAY_CODES.index(code))
    ordinal = int(ordinal_text)
    if match.group("sign") == "-":
        ordinal = -ordinal
    if ordinal == 0:
        raise RuleError("an ordinal of zero names no weekday: counting starts at 1 or at -1")
    if abs(ordinal) > 5:
        raise RuleError(f"ordinal {ordinal} is past the fifth weekday of any month")
    return ByDay(WEEKDAY_CODES.index(code), ordinal)


def parse_month_day(text: str) -> int:
    try:
        day = int(text)
    except ValueError as exc:
        raise RuleError(f"{text!r} is not a day of the month") from exc
    if not 1 <= day <= 31:
        raise RuleError(f"day of month {day} is outside 1..31")
    return day


def parse_month(text: str) -> int:
    try:
        month = int(text)
    except ValueError as exc:
        raise RuleError(f"{text!r} is not a month number") from exc
    if not 1 <= month <= 12:
        raise RuleError(f"month {month} is outside 1..12")
    return month


def parse_until(text: str) -> datetime:
    """UNTIL is an instant. A wall time without an offset is not one."""
    raw = text.strip()
    if raw.endswith(("Z", "z")):
        try:
            moment = datetime.strptime(raw[:-1], "%Y%m%dT%H%M%S")
        except ValueError as exc:
            raise RuleError(
                f"UNTIL={text!r} is not a UTC timestamp of the form 20260308T023000Z"
            ) from exc
        return moment.replace(tzinfo=UTC)
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise RuleError(f"UNTIL={text!r} is not an ISO timestamp") from exc
    if moment.tzinfo is None:
        raise RuleError(
            f"UNTIL={text!r} has no offset; an instant without an offset is a wall time, "
            "and a wall time means different instants in different zones"
        )
    return moment.astimezone(UTC)


@dataclass(frozen=True)
class Rule:
    """A parsed recurrence rule. Nothing here is expanded yet."""

    freq: str
    interval: int = 1
    count: int | None = None
    until: datetime | None = None
    byday: tuple[ByDay, ...] = field(default_factory=tuple)
    bymonthday: tuple[int, ...] = field(default_factory=tuple)
    bymonth: tuple[int, ...] = field(default_factory=tuple)
    wkst: int = 0
    text: str = ""

    @property
    def bounded(self) -> str:
        if self.count is not None:
            return f"COUNT={self.count}"
        if self.until is not None:
            return f"UNTIL={self.until.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        return "unbounded"

    def lines(self) -> list[str]:
        parts = [f"freq       {self.freq}", f"interval   {self.interval}"]
        if self.byday:
            parts.append(f"byday      {', '.join(entry.text for entry in self.byday)}")
        if self.bymonthday:
            parts.append(f"bymonthday {', '.join(str(day) for day in self.bymonthday)}")
        if self.bymonth:
            parts.append(f"bymonth    {', '.join(str(month) for month in self.bymonth)}")
        if self.freq == "WEEKLY":
            parts.append(f"wkst       {WEEKDAY_CODES[self.wkst]} ({WEEKDAY_NAMES[self.wkst]})")
        parts.append(f"bound      {self.bounded}")
        return parts

    def allows_month(self, month: int) -> bool:
        return not self.bymonth or month in self.bymonth

    def allows_month_day(self, year: int, month: int, day: int) -> bool:
        """BYMONTHDAY is a day number; months too short to hold it simply do not match."""
        if not self.bymonthday:
            return True
        return day in self.bymonthday and day <= days_in_month(year, month)


def _split_pairs(body: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for chunk in body.split(";"):
        piece = chunk.strip()
        if not piece:
            continue
        if "=" not in piece:
            raise RuleError(f"{piece!r} is not KEY=VALUE")
        key, _, value = piece.partition("=")
        key = key.strip().upper()
        if key not in KNOWN_KEYS:
            raise RuleError(f"unknown key {key}; this rule understands {', '.join(KNOWN_KEYS)}")
        pairs.append((key, value.strip()))
    if not pairs:
        raise RuleError("an empty rule repeats nothing")
    return pairs


def parse(text: str) -> Rule:
    """Parse a rule string; every key is checked, and impossible rules are refused."""
    body = text.strip()
    if body.upper().startswith(SECTION):
        body = body[len(SECTION) :]
    pairs = _split_pairs(body)
    seen: dict[str, str] = {}
    for key, value in pairs:
        if key in seen and key != "BYDAY":
            raise RuleError(f"{key} appears more than once; a rule states each key once")
        seen[key] = value if key not in seen else f"{seen[key]},{value}"
    if "FREQ" not in seen:
        raise RuleError("FREQ is required: a rule without a frequency repeats nothing")
    freq = seen["FREQ"].upper()
    if freq not in FREQS:
        raise RuleError(f"FREQ={seen['FREQ']!r} is not one of {', '.join(FREQS)}")
    interval = 1
    if "INTERVAL" in seen:
        try:
            interval = int(seen["INTERVAL"])
        except ValueError as exc:
            raise RuleError(f"INTERVAL={seen['INTERVAL']!r} is not a whole number") from exc
        if interval < 1:
            raise RuleError(f"INTERVAL={interval} would step backwards or stand still")
    count = None
    if "COUNT" in seen:
        try:
            count = int(seen["COUNT"])
        except ValueError as exc:
            raise RuleError(f"COUNT={seen['COUNT']!r} is not a whole number") from exc
        if count < 1:
            raise RuleError(f"COUNT={count} asks for no occurrences at all")
    until = parse_until(seen["UNTIL"]) if "UNTIL" in seen else None
    if count is not None and until is not None:
        raise RuleError("COUNT and UNTIL are two different endings; a rule has one")
    byday: list[ByDay] = []
    if "BYDAY" in seen:
        for piece in seen["BYDAY"].split(","):
            entry = parse_byday(piece)
            if entry in byday:
                raise RuleError(f"BYDAY names {entry.text} twice")
            if entry.ordinal is not None and freq != "MONTHLY" and freq != "YEARLY":
                raise RuleError(
                    f"ordinal {entry.text} counts within a month, and a {freq} rule "
                    "has no month to count in; use a plain weekday there"
                )
            byday.append(entry)
        if not byday:
            raise RuleError("BYDAY is present but names no weekday")
    bymonthday: list[int] = []
    if "BYMONTHDAY" in seen:
        if freq == "WEEKLY":
            raise RuleError("BYMONTHDAY on a WEEKLY rule asks for days the week does not choose")
        for piece in seen["BYMONTHDAY"].split(","):
            day = parse_month_day(piece)
            if day in bymonthday:
                raise RuleError(f"BYMONTHDAY names {day} twice")
            bymonthday.append(day)
    bymonth: list[int] = []
    if "BYMONTH" in seen:
        for piece in seen["BYMONTH"].split(","):
            month = parse_month(piece)
            if month in bymonth:
                raise RuleError(f"BYMONTH names {month} twice")
            bymonth.append(month)
        if bymonthday:
            shortest = {2: 29, 4: 30, 6: 30, 9: 30, 11: 30}
            reachable = [
                month
                for month in bymonth
                if any(day <= shortest.get(month, 31) for day in bymonthday)
            ]
            if not reachable:
                long_month = {2: "February", 4: "April", 6: "June", 9: "September", 11: "November"}
                designed = [
                    f"{long_month[month]} has {shortest.get(month, 31)} days" for month in bymonth
                ]
                raise RuleError(
                    f"BYMONTH with BYMONTHDAY={','.join(str(day) for day in bymonthday)} "
                    f"names no real date: {'; '.join(designed)}"
                )
    wkst = 0
    if "WKST" in seen:
        code = seen["WKST"].upper()
        if code not in WEEKDAY_CODES:
            raise RuleError(f"WKST={seen['WKST']!r} is not a weekday")
        wkst = WEEKDAY_CODES.index(code)
    return Rule(
        freq=freq,
        interval=interval,
        count=count,
        until=until,
        byday=tuple(byday),
        bymonthday=tuple(bymonthday),
        bymonth=tuple(bymonth),
        wkst=wkst,
        text=body,
    )

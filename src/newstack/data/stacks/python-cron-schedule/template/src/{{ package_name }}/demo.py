"""Six schedules where the answer is surprising until you see the calendar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from . import model


@dataclass(frozen=True)
class Step:
    scenario: str
    lines: tuple[str, ...]
    ok: bool

    def render(self) -> str:
        verdict = "as advertised" if self.ok else "NOT AS ADVERTISED"
        body = "\n".join(f"  {line}" for line in self.lines)
        return f"{self.scenario:<34} {verdict}\n{body}"


def _moment(text: str) -> datetime:
    return datetime.fromisoformat(text).astimezone(UTC)


def _starts() -> Step:
    schedule = model.parse("*/15 * * * *")
    runs = model.runs_after(schedule, _moment("2026-03-07T12:04:30+00:00"), "UTC", count=3)
    lines = tuple(f"next     {run.utc:%H:%M} UTC" for run in runs)
    ok = [run.utc.minute for run in runs] == [15, 30, 45]
    return Step("every fifteen minutes", lines, ok)


def _day_or() -> Step:
    schedule = model.parse("0 0 1 * 1")
    runs = model.runs_after(schedule, _moment("2026-03-03T00:00:00+00:00"), "UTC", count=5)
    lines = tuple(f"{run.utc:%Y-%m-%d %a}  {run.utc:%H:%M} UTC" for run in runs)
    weekdays = [run.utc.weekday() == 0 for run in runs[:-1]]
    ok = schedule.day_rule == "or" and all(weekdays) and runs[-1].utc.day == 1
    return Step("day 1 or Monday, not both", lines, ok)


def _spring_forward() -> Step:
    schedule = model.parse("30 2 * * *")
    runs = model.runs_after(
        schedule, _moment("2026-03-07T12:00:00+00:00"), "America/New_York", count=2
    )
    before = model.first_after(schedule, _moment("2026-03-06T12:00:00+00:00"), "America/New_York")
    lines = (
        f"the run before   {before.local:%Y-%m-%d %H:%M %Z}  ({before.utc:%H:%M} UTC)",
        f"next run         {runs[0].local:%Y-%m-%d %H:%M %Z}  ({runs[0].utc:%H:%M} UTC)",
        "2026-03-08 02:30 does not exist in New York, so that day has no run",
        f"the gap between them is {int((runs[0].utc - before.utc).total_seconds() // 3600)} hours",
    )
    ok = (
        before.utc.date().isoformat() == "2026-03-07"
        and runs[0].utc.date().isoformat() == "2026-03-09"
        and int((runs[0].utc - before.utc).total_seconds() // 3600) == 47
    )
    return Step("the hour that never happens", lines, ok)


def _fall_back() -> Step:
    schedule = model.parse("30 1 * * *")
    runs = model.runs_after(
        schedule, _moment("2026-10-31T12:00:00+00:00"), "America/New_York", count=3
    )
    lines = tuple(f"{run.utc:%Y-%m-%dT%H:%M:%SZ}  {run.local:%Y-%m-%d %H:%M %Z}" for run in runs)
    same_day_twice = (
        runs[0].utc.date() == runs[1].utc.date()
        and runs[0].local.hour == runs[1].local.hour == 1
        and runs[1].utc - runs[0].utc == (runs[1].utc - runs[0].utc)
        and (runs[1].utc - runs[0].utc).total_seconds() == 3600
    )
    lines = (*lines, "01:30 happens twice on 2026-11-01, so the job runs twice")
    return Step("the hour that happens twice", lines, same_day_twice)


def _zero_step() -> Step:
    try:
        model.parse("*/0 * * * *")
    except model.CronError as error:
        return Step("a step of zero", (f"refused   {error}",), True)
    return Step("a step of zero", ("accepted a schedule that can never fire",), False)


def _sunday() -> Step:
    saturday = model.parse("0 0 * * 7")
    sunday = model.parse("0 0 * * 0")
    same = saturday.weekday.values == sunday.weekday.values
    run = model.first_after(sunday, _moment("2026-03-03T00:00:00+00:00"), "UTC")
    day = f"{run.utc:%Y-%m-%d %a}" if run else "(nothing)"
    lines = (
        f"weekday 7 -> values {sorted(saturday.weekday.values)}",
        f"weekday 0 -> values {sorted(sunday.weekday.values)}",
        f"the same schedule, and the next run is {day}",
    )
    return Step("Sunday is 0 and 7", lines, same and run is not None and run.utc.weekday() == 6)


def run() -> list[Step]:
    return [_starts(), _day_or(), _spring_forward(), _fall_back(), _zero_step(), _sunday()]


def render(steps: list[Step]) -> str:
    report = "\n\n".join(step.render() for step in steps)
    missed = sum(1 for step in steps if not step.ok)
    return f"{report}\n\ndemo: {len(steps)} schedules, {missed} not as advertised"


def payload(steps: list[Step]) -> dict[str, object]:
    return {
        "steps": [
            {"scenario": step.scenario, "lines": list(step.lines), "ok": step.ok} for step in steps
        ],
        "ok": all(step.ok for step in steps),
    }

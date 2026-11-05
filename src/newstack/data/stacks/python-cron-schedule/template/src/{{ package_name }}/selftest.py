"""The claims of this stack, checked with no server, no clock and no prose."""

from __future__ import annotations

from datetime import UTC, datetime

from . import demo, model


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
        except (model.CronError, ValueError):
            self.passed += 1
            return
        except Exception as error:
            self.failed += 1
            print(f"FAIL  {description} raised {type(error).__name__}: {error}")
            return
        self.failed += 1
        print(f"FAIL  {description} did not raise")


def _moment(text: str) -> datetime:
    return datetime.fromisoformat(text).astimezone(UTC)


def _fifteen() -> list[int]:
    schedule = model.parse("*/15 * * * *")
    runs = model.runs_after(schedule, _moment("2026-03-07T12:04:30+00:00"), "UTC", count=3)
    return [run.utc.minute for run in runs]


def _field_checks(checks: Checks) -> None:
    checks.equal("*/15 is four values", 4, len(model.parse("*/15 * * * *").minute.values))
    checks.equal("1-5 is five values", 5, len(model.parse("1-5 * * * *").minute.values))
    checks.equal(
        "mon-fri is Monday to Friday",
        frozenset({1, 2, 3, 4, 5}),
        model.parse("0 0 * * mon-fri").weekday.values,
    )
    checks.equal("7 means Sunday", frozenset({0}), model.parse("0 0 * * 7").weekday.values)
    checks.equal(
        "10-20/5 steps through the range",
        frozenset({10, 15, 20}),
        model.parse("10-20/5 * * * *").minute.values,
    )
    checks.ok("a star field knows it is a star", model.parse("* * * * *").minute.star)
    checks.ok("*/15 is not the whole range", not model.parse("*/15 * * * *").minute.star)
    checks.equal("month names work", frozenset({1, 2}), model.parse("0 0 * jan,feb *").month.values)


def _refusal_checks(checks: Checks) -> None:
    for text in (
        "* * * *",
        "* * * * * *",
        "60 * * * *",
        "* 24 * * *",
        "* * 0 * *",
        "* * * 13 *",
        "* * * * 8",
        "*/0 * * * *",
        "5-1 * * * *",
        "",
        "abc * * * *",
        "* * * smarch *",
    ):
        checks.raises(f"{text!r} is refused", model.parse, text)


def _semantics_checks(checks: Checks) -> None:
    schedule = model.parse("0 9 * * mon-fri")
    checks.ok(
        "Monday 09:00 local matches",
        schedule.matches(datetime(2026, 3, 9, 9, 0, tzinfo=UTC)),
    )
    checks.ok(
        "Saturday 09:00 does not",
        not schedule.matches(datetime(2026, 3, 7, 9, 0, tzinfo=UTC)),
    )
    checks.equal("one restricted field means AND", "and", schedule.day_rule)
    both = model.parse("0 0 1 * 1")
    checks.equal("two restricted fields mean OR", "or", both.day_rule)
    checks.ok(
        "the 1st matches even when it is a Wednesday",
        both.matches(datetime(2026, 4, 1, 0, 0, tzinfo=UTC)),
    )
    checks.ok(
        "a Monday matches even when it is not the 1st",
        both.matches(datetime(2026, 3, 9, 0, 0, tzinfo=UTC)),
    )
    checks.ok(
        "a Tuesday that is not the 1st does not match",
        not both.matches(datetime(2026, 3, 10, 0, 0, tzinfo=UTC)),
    )
    checks.equal("every fifteen minutes, three of them", [15, 30, 45], _fifteen())


def _window_checks(checks: Checks) -> None:
    schedule = model.parse("*/15 * * * *")
    after = _moment("2026-03-07T12:15:00+00:00")
    runs = model.runs_after(schedule, after, "UTC", count=2)
    checks.ok("a run exactly at --after is not returned", runs[0].utc > after)
    checks.ok("the runs are strictly increasing", runs[0].utc < runs[1].utc)
    checks.raises(
        "a naive moment is refused", model.runs_after, schedule, datetime(2026, 3, 7, 12, 0), "UTC"
    )
    checks.raises("count 0 is refused", model.runs_after, schedule, after, "UTC", count=0)
    checks.raises("an unknown zone is refused", model.runs_after, schedule, after, "Mars/Olympus")
    nothing = model.parse("0 0 30 2 *")
    checks.equal("February 30 has no run", [], model.runs_after(nothing, after, "UTC", count=1))


def _dst_checks(checks: Checks) -> None:
    spring = model.parse("30 2 * * *")
    runs = model.runs_after(
        spring, _moment("2026-03-07T12:00:00+00:00"), "America/New_York", count=1
    )
    checks.equal(
        "02:30 skips the day it does not exist", "2026-03-09", runs[0].utc.date().isoformat()
    )
    checks.equal("and lands on the same wall clock", "02:30", f"{runs[0].local:%H:%M}")
    before = model.first_after(spring, _moment("2026-03-06T12:00:00+00:00"), "America/New_York")
    gap = int((runs[0].utc - before.utc).total_seconds() // 3600)
    checks.equal("the gap across the change is 47 hours", 47, gap)
    fall = model.parse("30 1 * * *")
    twice = model.runs_after(
        fall, _moment("2026-10-31T12:00:00+00:00"), "America/New_York", count=2
    )
    checks.equal("01:30 runs twice on 2026-11-01", "2026-11-01", twice[0].utc.date().isoformat())
    checks.equal(
        "the second run is one hour later", 3600, int((twice[1].utc - twice[0].utc).total_seconds())
    )
    checks.ok(
        "the wall clock reads the same both times",
        f"{twice[0].local:%H:%M}" == f"{twice[1].local:%H:%M}" == "01:30",
    )
    checks.ok(
        "the offsets differ, which is why", twice[0].local.utcoffset() != twice[1].local.utcoffset()
    )


def _demo_checks(checks: Checks) -> None:
    steps = demo.run()
    checks.equal("six schedules", 6, len(steps))
    for step in steps:
        checks.ok(f"{step.scenario} is as advertised", step.ok)
    checks.ok("the demo's own report says so", "0 not as advertised" in demo.render(steps))


def run() -> int:
    checks = Checks()
    for group in (
        _field_checks,
        _refusal_checks,
        _semantics_checks,
        _window_checks,
        _dst_checks,
        _demo_checks,
    ):
        group(checks)
    total = checks.passed + checks.failed
    print(f"selftest: {checks.passed} checks passed, {checks.failed} failed out of {total}")
    return 0 if checks.failed == 0 else 1

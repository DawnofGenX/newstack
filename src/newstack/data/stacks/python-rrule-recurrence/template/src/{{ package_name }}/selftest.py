"""Known answers, checked without pytest: the same arithmetic a reviewer would do by hand."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from . import cli as cli_module
from . import demo as demo_module
from .expand import expand
from .explain import explain
from .rrule import RuleError, parse

FIXTURES = Path(__file__).resolve().parent.parent.parent / "fixtures"
NY = ZoneInfo("America/New_York")
KOLKATA = ZoneInfo("Asia/Kolkata")


@dataclass
class Report:
    checks: int = 0
    failed: int = 0
    lines: list[str] = field(default_factory=list)

    def ok(self, claim: str, held: bool) -> None:
        self.checks += 1
        if not held:
            self.failed += 1
        self.lines.append(f"  {'ok  ' if held else 'FAIL'} {claim}")

    def equal(self, claim: str, found: object, expected: object) -> None:
        self.ok(f"{claim}: {found!r} == {expected!r}", found == expected)

    def refuses(self, claim: str, rule_text: str, needle: str) -> None:
        try:
            parse(rule_text)
        except RuleError as error:
            self.ok(f"{claim}: {needle}", needle in str(error))
        else:
            self.ok(f"{claim}: accepted {rule_text}, which it should not", False)

    def section(self, title: str) -> None:
        self.lines.append(f"{title}")


def _dates(rule_text: str, start: datetime, zone: ZoneInfo = NY, **kwargs) -> list[str]:
    result = expand(parse(rule_text), start, zone, **kwargs)
    return [item.local.strftime("%Y-%m-%d %H:%M") for item in result.occurrences]


def _syntax(report: Report) -> None:
    report.section("syntax")
    rule = parse("RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE;COUNT=6;WKST=SU")
    report.equal("freq", rule.freq, "WEEKLY")
    report.equal("interval", rule.interval, 2)
    report.equal("count", rule.count, 6)
    report.equal("wkst", rule.wkst, 6)
    report.equal("byday", [entry.text for entry in rule.byday], ["MO", "WE"])
    report.equal("bounded", rule.bounded, "COUNT=6")
    report.equal("unbounded", parse("FREQ=DAILY").bounded, "unbounded")
    report.equal(
        "until is read as utc",
        parse("FREQ=DAILY;UNTIL=20260303T033000Z").until.isoformat(),
        "2026-03-03T03:30:00+00:00",
    )
    report.equal(
        "an offset until is converted",
        parse("FREQ=DAILY;UNTIL=20260303T090000+05:30").until.hour,
        3,
    )


def _refusals(report: Report) -> None:
    report.section("refusals")
    report.refuses("no frequency", "COUNT=3", "FREQ is required")
    report.refuses(
        "two endings", "FREQ=DAILY;COUNT=2;UNTIL=20260303T033000Z", "two different endings"
    )
    report.refuses(
        "wall-time until", "FREQ=DAILY;UNTIL=20260303T033000", "instant without an offset"
    )
    report.refuses("zero interval", "FREQ=DAILY;INTERVAL=0", "stand still")
    report.refuses("zero count", "FREQ=DAILY;COUNT=0", "no occurrences")
    report.refuses("unknown key", "FREQ=DAILY;BYHOUR=9", "BYHOUR")
    report.refuses("ordinal on a weekly rule", "FREQ=WEEKLY;BYDAY=1MO", "no month to count in")
    report.refuses("ordinal past five", "FREQ=MONTHLY;BYDAY=6MO", "past the fifth weekday")
    report.refuses("zero ordinal", "FREQ=MONTHLY;BYDAY=0MO", "counting starts at 1")
    report.refuses("byday twice", "FREQ=WEEKLY;BYDAY=MO,MO", "twice")
    report.refuses(
        "bymonthday on weekly", "FREQ=WEEKLY;BYMONTHDAY=1", "days the week does not choose"
    )
    report.refuses("february 30th", "FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=30", "no real date")
    report.refuses("a bad frequency", "FREQ=SOMETIMES", "is not one of")


def _calendar(report: Report) -> None:
    report.section("calendar")
    weekly = _dates("FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=5", datetime(2026, 1, 5, 9, 0))
    report.equal("five firings across two weeks", len(weekly), 5)
    report.equal("the fifth is a Wednesday", weekly[-1], "2026-01-14 09:00")
    shifted = _dates("FREQ=WEEKLY;INTERVAL=2;BYDAY=TU;COUNT=2", datetime(2026, 1, 13, 9, 0))
    report.equal("a shifted start picks the other weeks", shifted[0], "2026-01-13 09:00")
    last_friday = _dates("FREQ=MONTHLY;BYDAY=-1FR;COUNT=3", datetime(2026, 1, 1, 9, 0))
    report.equal(
        "the last friday of january 2026",
        [item[:10] for item in last_friday],
        ["2026-01-30", "2026-02-27", "2026-03-27"],
    )
    first_monday = _dates("FREQ=MONTHLY;BYDAY=1MO;COUNT=2", datetime(2026, 1, 1, 9, 0))
    report.equal("january 2026 starts on a thursday", first_monday[0], "2026-01-05 09:00")
    short_months = _dates("FREQ=MONTHLY;COUNT=3", datetime(2026, 1, 31, 12, 0))
    report.equal(
        "months without a 31st are skipped",
        [item[:7] for item in short_months],
        ["2026-01", "2026-03", "2026-05"],
    )
    leap = _dates("FREQ=YEARLY;COUNT=2", datetime(2024, 2, 29, 12, 0))
    report.equal("leap day repeats every four years", leap[1], "2028-02-29 12:00")
    bounded = _dates("FREQ=DAILY;UNTIL=20260303T033000Z", datetime(2026, 3, 1, 9, 0), KOLKATA)
    report.equal("until is inclusive", len(bounded), 3)
    earlier = _dates("FREQ=DAILY;UNTIL=20260303T032900Z", datetime(2026, 3, 1, 9, 0), KOLKATA)
    report.equal("one minute earlier drops the boundary", len(earlier), 2)


def _zones(report: Report) -> None:
    report.section("zones")
    spring = expand(parse("FREQ=DAILY;COUNT=4"), datetime(2026, 3, 6, 2, 30), NY)
    report.equal(
        "the 8th of march has no 02:30",
        [item.local.day for item in spring.occurrences],
        [6, 7, 9, 10],
    )
    report.equal("one wall time was skipped", len(spring.skipped), 1)
    report.ok("the skip names the jump", "jumped forward" in spring.skipped[0].reason)
    autumn = expand(parse("FREQ=DAILY;COUNT=3"), datetime(2026, 10, 31, 1, 30), NY)
    report.equal("the repeated hour fires once", len(autumn.skipped), 0)
    gaps = [
        (b.instant - a.instant).total_seconds() / 3600
        for a, b in zip(autumn.occurrences, autumn.occurrences[1:], strict=False)
    ]
    report.equal("the long night comes after the short one", gaps, [24.0, 25.0])
    day = expand(parse("FREQ=DAILY;COUNT=2"), datetime(2026, 3, 7, 3, 30), NY)
    span = (day.occurrences[1].instant - day.occurrences[0].instant).total_seconds() / 3600
    report.equal("the spring night is 23 hours", span, 23.0)
    utc = expand(parse("FREQ=DAILY;COUNT=2"), datetime(2026, 7, 1, 9, 0), NY)
    report.equal(
        "a summer wall time maps to edt",
        utc.occurrences[0].instant.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "2026-07-01T13:00:00Z",
    )
    report.equal(
        "and to est in january",
        expand(parse("FREQ=DAILY;COUNT=1"), datetime(2026, 1, 1, 9, 0), NY)
        .occurrences[0]
        .instant.strftime("%H:%M"),
        "14:00",
    )


def _explanations(report: Report) -> None:
    report.section("explanations")
    admitted = explain(
        parse("FREQ=WEEKLY;BYDAY=MO"), datetime(2026, 1, 5, 9, 0), NY, datetime(2026, 1, 12, 9, 0)
    )
    report.ok("a monday explains itself", admitted.occurrence)
    wrong_day = explain(
        parse("FREQ=WEEKLY;BYDAY=MO"), datetime(2026, 1, 5, 9, 0), NY, datetime(2026, 1, 7, 9, 0)
    )
    report.ok("a wednesday against BYDAY=MO is refused", not wrong_day.occurrence)
    report.ok("and the reason names the weekday", "Wednesday" in wrong_day.reasons[0])
    off_week = explain(
        parse("FREQ=WEEKLY;INTERVAL=2;BYDAY=MO"),
        datetime(2026, 1, 5, 9, 0),
        NY,
        datetime(2026, 1, 12, 9, 0),
    )
    report.ok("an off week is counted in periods", "1 period(s)" in off_week.reasons[0])
    gap = explain(parse("FREQ=DAILY"), datetime(2026, 3, 6, 2, 30), NY, datetime(2026, 3, 8, 2, 30))
    report.ok("the spring gap is explained", "gap the zone made" in gap.reasons[0])
    past = explain(
        parse("FREQ=DAILY;UNTIL=20260303T033000Z"),
        datetime(2026, 3, 1, 9, 0),
        KOLKATA,
        datetime(2026, 3, 4, 9, 0),
    )
    report.ok("an instant past until is refused", "past UNTIL" in past.reasons[0])
    report.equal("lines name the moment", gap.lines()[0], "at         2026-03-08 02:30:00")


def _stories(report: Report) -> None:
    report.section("stories")
    lines = demo_module.render_stories()
    report.equal("all six stories hold", lines[-1], "stories      6 of 6 hold")
    for story in demo_module.stories():
        report.ok(f"story {story.number} holds: {story.title}", story.held())


def _fixture(report: Report) -> None:
    report.section("fixtures")
    rows = [
        line
        for line in (FIXTURES / "rules.txt").read_text().splitlines()
        if line and not line.startswith("#")
    ]
    report.equal("five rules in the fixture", len(rows), 5)
    expanded = 0
    for row in rows:
        rule_text, start_text, zone, _ = [part.strip() for part in row.split("|")]
        result = expand(
            parse(rule_text), datetime.fromisoformat(start_text), ZoneInfo(zone), limit=4
        )
        expanded += 1 if result.occurrences else 0
    report.equal("every fixture rule fires", expanded, 5)


def _command_line(report: Report) -> None:
    report.section("command line")
    parser = cli_module.build_parser()
    report.ok(
        "demo routes to demo", parser.parse_args(["demo"]).handler is cli_module._command_demo
    )
    report.ok(
        "selftest routes to selftest",
        parser.parse_args(["selftest"]).handler is cli_module._command_selftest,
    )
    parsed = parser.parse_args(
        [
            "explain",
            "--rule",
            "FREQ=DAILY",
            "--start",
            "2026-01-01T00:00",
            "--at",
            "2026-01-02T00:00",
        ]
    )
    report.equal("explain keeps the moment it was asked about", parsed.at, "2026-01-02T00:00")
    report.equal("the version is set", cli_module.VERSION, "0.1.0")
    report.equal(
        "exit codes are distinct",
        (cli_module.EXIT_OK, cli_module.EXIT_NO_MATCH, cli_module.EXIT_UNUSABLE),
        (0, 1, 2),
    )


def run() -> int:
    report = Report()
    _syntax(report)
    _refusals(report)
    _calendar(report)
    _zones(report)
    _explanations(report)
    _stories(report)
    _fixture(report)
    _command_line(report)
    for line in report.lines:
        print(line)
    if report.failed:
        print(f"selftest: {report.checks} checks, {report.failed} failed")
        return 1
    print(f"selftest: {report.checks} checks passed, 0 failed")
    return 0

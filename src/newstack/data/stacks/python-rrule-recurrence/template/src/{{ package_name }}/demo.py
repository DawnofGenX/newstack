"""Six stories about what a recurrence rule actually promises."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from .expand import expand
from .rrule import RuleError, parse

NY = ZoneInfo("America/New_York")
KOLKATA = ZoneInfo("Asia/Kolkata")


@dataclass
class Story:
    number: int
    title: str
    lines: list[str] = field(default_factory=list)
    claims: list[tuple[str, bool]] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.lines.append(f"  {text}")

    def require(self, claim: str, held: bool) -> None:
        self.claims.append((claim, held))
        self.lines.append(f"  {claim}: {'yes' if held else 'NO'}")

    def held(self) -> bool:
        return all(held for _, held in self.claims)


def _dates(rule_text: str, start: datetime, zone: ZoneInfo = NY, **kwargs) -> list[str]:
    result = expand(parse(rule_text), start, zone, **kwargs)
    return [item.local.strftime("%Y-%m-%d %H:%M") for item in result.occurrences]


def story_one() -> Story:
    story = Story(1, "COUNT counts firings, not intervals")
    firings = _dates("FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=5", datetime(2026, 1, 5, 9, 0))
    story.say("rule   FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=5 from Mon 2026-01-05 09:00")
    story.say(f"fired  {', '.join(firings)}")
    story.say("COUNT=5 stopped inside the second week, not at the second Monday")
    story.require("five firings", len(firings) == 5)
    story.require(
        "three of them are in the first week", sum(d.startswith("2026-01-0") for d in firings) == 3
    )
    story.require("the last one is in the second week", firings[-1].startswith("2026-01-14"))
    return story


def story_two() -> Story:
    story = Story(2, "INTERVAL is counted from the start's own week")
    first = _dates("FREQ=WEEKLY;INTERVAL=2;BYDAY=TU;COUNT=3", datetime(2026, 1, 6, 9, 0))
    shifted = _dates("FREQ=WEEKLY;INTERVAL=2;BYDAY=TU;COUNT=3", datetime(2026, 1, 13, 9, 0))
    story.say(f"start Tue 2026-01-06  {', '.join(first)}")
    story.say(f"start Tue 2026-01-13  {', '.join(shifted)}")
    story.say("a week later, the whole series lands on the other weeks")
    story.require("the first two firings are a fortnight apart", first[1].startswith("2026-01-20"))
    story.require(
        "shifting the start by 7 days shifts every firing", shifted[0].startswith("2026-01-13")
    )
    story.require("the two series never share a week", set(first).isdisjoint(shifted))
    return story


def story_three() -> Story:
    story = Story(3, "an ordinal weekday counts from the edges of the month")
    last_friday = _dates("FREQ=MONTHLY;BYDAY=-1FR;COUNT=4", datetime(2026, 1, 1, 9, 0))
    first_monday = _dates("FREQ=MONTHLY;BYDAY=1MO;COUNT=4", datetime(2026, 1, 1, 9, 0))
    story.say(f"last Friday  {', '.join(last_friday)}")
    story.say(f"first Monday {', '.join(first_monday)}")
    story.say("January 2026 starts on a Thursday, so the first Monday is the 5th, not the 1st")
    story.require(
        "the last Friday of January 2026 is the 30th", last_friday[0].startswith("2026-01-30")
    )
    story.require("the first Monday is the 5th", first_monday[0].startswith("2026-01-05"))
    story.require("one firing per month in both series", len({d[:7] for d in last_friday}) == 4)
    return story


def story_four() -> Story:
    story = Story(4, "UNTIL is an instant, and it is inclusive")
    firings = _dates("FREQ=DAILY;UNTIL=20260303T033000Z", datetime(2026, 3, 1, 9, 0), KOLKATA)
    story.say("rule   FREQ=DAILY;UNTIL=20260303T033000Z from 2026-03-01 09:00 Asia/Kolkata")
    story.say(f"fired  {', '.join(firings)}")
    story.say("09:00 in Kolkata is 03:30Z, so the third firing lands exactly on UNTIL")
    story.require("the boundary day fires", firings[-1].startswith("2026-03-03"))
    story.require("three firings, not four", len(firings) == 3)
    story.require("nothing after it", all(d < "2026-03-04" for d in firings))
    return story


def story_five() -> Story:
    story = Story(5, "a wall time that the zone never showed is skipped, not guessed")
    spring = expand(parse("FREQ=DAILY;COUNT=4"), datetime(2026, 3, 6, 2, 30), NY)
    shown = ", ".join(item.local.strftime("%m-%d %H:%M") for item in spring.occurrences)
    first_skip = spring.skipped[0].local.strftime("%Y-%m-%d %H:%M") if spring.skipped else "-"
    story.say(f"02:30 daily from 2026-03-06: {shown}")
    story.say(f"skipped: {len(spring.skipped)} ({first_skip})")
    story.require("March 8th 02:30 never happens", len(spring.skipped) == 1)
    story.require("the count is still four firings", len(spring.occurrences) == 4)
    story.require("the last one is the 10th", spring.occurrences[-1].local.day == 10)
    three_thirty = expand(parse("FREQ=DAILY;COUNT=3"), datetime(2026, 3, 7, 3, 30), NY)
    gaps = [
        (b.instant - a.instant).total_seconds() / 3600
        for a, b in zip(three_thirty.occurrences, three_thirty.occurrences[1:], strict=False)
    ]
    story.say(f"03:30 daily across the same night: gaps {[round(gap, 1) for gap in gaps]} hours")
    story.require("the spring night is 23 hours long", gaps[0] == 23)
    return story


def story_six() -> Story:
    story = Story(6, "February 29 is a date that mostly does not exist")
    firings = _dates("FREQ=YEARLY;COUNT=3", datetime(2024, 2, 29, 12, 0))
    story.say(f"yearly from 2024-02-29: {', '.join(firings)}")
    story.require("the next firing is four years later", firings[1].startswith("2028-02-29"))
    story.require("2025, 2026 and 2027 are skipped silently", len(firings) == 3)
    refused = ""
    try:
        parse("FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=30")
    except RuleError as error:
        refused = str(error)
    story.say(f"refused: {refused}")
    story.require("a rule that can never fire is refused at parse time", "no real date" in refused)
    return story


def stories() -> list[Story]:
    return [story_one(), story_two(), story_three(), story_four(), story_five(), story_six()]


def render_stories() -> list[str]:
    lines: list[str] = []
    total = 0
    held = 0
    for story in stories():
        total += 1
        if story.held():
            held += 1
        lines.append(f"{story.number}. {story.title}")
        lines.extend(story.lines)
        lines.append(f"  -> {'holds' if story.held() else 'BROKEN'}")
        lines.append("")
    if held == total:
        lines.append(f"stories      {total} of {total} hold")
    else:
        lines.append(f"stories      BROKEN: {total - held} of {total} do not hold")
    return lines


def run() -> int:
    for line in render_stories():
        print(line)
    return 0 if all(story.held() for story in stories()) else 1

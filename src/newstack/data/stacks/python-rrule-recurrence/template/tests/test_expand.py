"""Expansion: the calendar arithmetic, including the parts a zone gets to cancel."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from {{ package_name }} import expand as module
from {{ package_name }} import rrule as subject

NY = ZoneInfo("America/New_York")
KOLKATA = ZoneInfo("Asia/Kolkata")
SYDNEY = ZoneInfo("Australia/Sydney")


def dates(rule_text, start, zone=NY, **kwargs):
    result = module.expand(subject.parse(rule_text), start, zone, **kwargs)
    return [item.local.strftime("%Y-%m-%d %H:%M") for item in result.occurrences]


def test_a_weekly_byday_rule_walks_the_week_it_is_given():
    found = dates("FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=5", datetime(2026, 1, 5, 9, 0))
    assert found == [
        "2026-01-05 09:00",
        "2026-01-07 09:00",
        "2026-01-09 09:00",
        "2026-01-12 09:00",
        "2026-01-14 09:00",
    ]


def test_count_counts_firings_not_periods():
    found = dates("FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=5", datetime(2026, 1, 5, 9, 0))
    assert len(found) == 5
    assert found[-1].startswith("2026-01-14")


def test_interval_is_anchored_to_the_start_week():
    first = dates("FREQ=WEEKLY;INTERVAL=2;BYDAY=TU;COUNT=3", datetime(2026, 1, 6, 9, 0))
    shifted = dates("FREQ=WEEKLY;INTERVAL=2;BYDAY=TU;COUNT=3", datetime(2026, 1, 13, 9, 0))
    assert first == ["2026-01-06 09:00", "2026-01-20 09:00", "2026-02-03 09:00"]
    assert set(first).isdisjoint(shifted)


def test_wkst_moves_the_week_boundary_and_so_which_monday_fires():
    monday_week = dates(
        "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO;WKST=MO;COUNT=2", datetime(2026, 1, 4, 9, 0)
    )
    sunday_week = dates(
        "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO;WKST=SU;COUNT=2", datetime(2026, 1, 4, 9, 0)
    )
    assert monday_week == ["2026-01-12 09:00", "2026-01-26 09:00"]
    assert sunday_week == ["2026-01-05 09:00", "2026-01-19 09:00"]


def test_the_last_friday_is_measured_from_the_end_of_the_month():
    found = dates("FREQ=MONTHLY;BYDAY=-1FR;COUNT=4", datetime(2026, 1, 1, 9, 0))
    assert [item[:10] for item in found] == ["2026-01-30", "2026-02-27", "2026-03-27", "2026-04-24"]


def test_the_first_monday_is_measured_from_the_first_day():
    found = dates("FREQ=MONTHLY;BYDAY=1MO;COUNT=4", datetime(2026, 1, 1, 9, 0))
    assert [item[:10] for item in found] == ["2026-01-05", "2026-02-02", "2026-03-02", "2026-04-06"]


def test_a_month_without_the_named_day_is_skipped():
    found = dates("FREQ=MONTHLY;COUNT=4", datetime(2026, 1, 31, 12, 0))
    assert [item[:7] for item in found] == ["2026-01", "2026-03", "2026-05", "2026-07"]


def test_a_yearly_rule_keeps_the_start_month_and_day():
    found = dates("FREQ=YEARLY;COUNT=3", datetime(2024, 2, 29, 12, 0))
    assert [item[:10] for item in found] == ["2024-02-29", "2028-02-29", "2032-02-29"]


def test_until_is_inclusive_and_compared_as_an_instant():
    found = dates("FREQ=DAILY;UNTIL=20260303T033000Z", datetime(2026, 3, 1, 9, 0), KOLKATA)
    assert found == ["2026-03-01 09:00", "2026-03-02 09:00", "2026-03-03 09:00"]


def test_until_one_minute_earlier_drops_the_boundary():
    found = dates("FREQ=DAILY;UNTIL=20260303T032900Z", datetime(2026, 3, 1, 9, 0), KOLKATA)
    assert len(found) == 2


def test_the_spring_gap_skips_the_wall_time_it_swallowed():
    result = module.expand(subject.parse("FREQ=DAILY;COUNT=4"), datetime(2026, 3, 6, 2, 30), NY)
    assert [item.local.day for item in result.occurrences] == [6, 7, 9, 10]
    assert len(result.skipped) == 1
    assert result.skipped[0].local.day == 8
    assert "jumped forward" in result.skipped[0].reason


def test_a_skipped_wall_time_does_not_use_up_the_count():
    result = module.expand(subject.parse("FREQ=DAILY;COUNT=4"), datetime(2026, 3, 6, 2, 30), NY)
    assert result.occurrences[-1].local.day == 10
    assert len(result.occurrences) == 4


def test_a_time_that_exists_gains_the_short_night_as_a_23_hour_gap():
    result = module.expand(subject.parse("FREQ=DAILY;COUNT=3"), datetime(2026, 3, 7, 3, 30), NY)
    gaps = [
        (b.instant - a.instant).total_seconds() / 3600
        for a, b in zip(result.occurrences, result.occurrences[1:], strict=False)
    ]
    assert gaps == [23.0, 24.0]


def test_the_autumn_hour_that_happens_twice_fires_once():
    result = module.expand(subject.parse("FREQ=DAILY;COUNT=3"), datetime(2026, 10, 31, 1, 30), NY)
    assert [item.local.strftime("%m-%d %H") for item in result.occurrences] == [
        "10-31 01",
        "11-01 01",
        "11-02 01",
    ]
    gaps = [
        (b.instant - a.instant).total_seconds() / 3600
        for a, b in zip(result.occurrences, result.occurrences[1:], strict=False)
    ]
    assert gaps == [24.0, 25.0]


def test_southern_hemisphere_spring_falls_in_october():
    result = module.expand(
        subject.parse("FREQ=DAILY;COUNT=3"), datetime(2026, 10, 3, 2, 30), SYDNEY
    )
    assert [item.local.day for item in result.occurrences] == [3, 5, 6]
    assert len(result.skipped) == 1


def test_a_rule_that_cannot_fire_says_so_instead_of_looping():
    result = module.expand(
        subject.parse("FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=29"),
        datetime(2025, 3, 1, 0, 0),
        NY,
        span_years=1,
    )
    assert not result.occurrences
    assert "no occurrence within 1 years" in result.stopped


def test_the_limit_stops_the_walk_early():
    result = module.expand(subject.parse("FREQ=DAILY"), datetime(2026, 1, 1, 0, 0), NY, limit=3)
    assert len(result.occurrences) == 3
    assert result.stopped == "limit 3 reached"


def test_a_start_with_an_offset_is_refused_because_rules_name_wall_times():
    with pytest.raises(subject.RuleError, match="wall time in a zone"):
        module.expand(subject.parse("FREQ=DAILY"), datetime(2026, 1, 1, tzinfo=NY), NY)


def test_between_keeps_only_the_window():
    window = module.between(
        subject.parse("FREQ=DAILY;COUNT=10"),
        datetime(2026, 1, 1, 0, 0),
        NY,
        after=datetime(2026, 1, 3, 0, 0),
        before=datetime(2026, 1, 5, 0, 0),
    )
    assert [item.local.day for item in window.occurrences] == [3, 4, 5]


def test_occurrences_are_strictly_increasing_in_utc():
    result = module.expand(
        subject.parse("FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;COUNT=40"), datetime(2026, 1, 1, 8, 0), NY
    )
    instants = [item.instant for item in result.occurrences]
    assert instants == sorted(instants)
    assert len(set(instants)) == len(instants)


def test_the_expansion_reports_the_rule_it_used():
    result = module.expand(subject.parse("FREQ=DAILY;COUNT=1"), datetime(2026, 1, 1, 0, 0), NY)
    assert result.rule.text == "FREQ=DAILY;COUNT=1"
    assert result.lines()[-1].startswith("stopped")

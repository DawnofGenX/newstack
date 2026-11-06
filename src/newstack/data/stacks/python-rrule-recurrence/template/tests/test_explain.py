"""The explanations come from the same machinery, so they cannot drift from it."""

from datetime import datetime
from zoneinfo import ZoneInfo

from {{ package_name }} import explain as module
from {{ package_name }} import rrule as subject

NY = ZoneInfo("America/New_York")


def decide(rule_text, start, at, zone=NY):
    return module.explain(subject.parse(rule_text), start, zone, at)


def test_an_occurrence_is_admitted_without_excuses():
    decision = decide(
        "FREQ=WEEKLY;BYDAY=MO,WE;COUNT=4", datetime(2026, 1, 5, 9, 0), datetime(2026, 1, 7, 9, 0)
    )
    assert decision.occurrence
    assert decision.reasons == [
        "every filter in the rule admits it",
        "COUNT=4 is a bound on the series, not a filter on one date",
    ]


def test_a_wrong_hour_is_named_before_anything_else():
    decision = decide("FREQ=DAILY", datetime(2026, 1, 5, 9, 0), datetime(2026, 1, 6, 10, 0))
    assert not decision.occurrence
    assert "fires at 09:00:00" in decision.reasons[0]


def test_a_wrong_weekday_is_refused_by_name():
    decision = decide(
        "FREQ=WEEKLY;BYDAY=MO", datetime(2026, 1, 5, 9, 0), datetime(2026, 1, 7, 9, 0)
    )
    assert not decision.occurrence
    assert "Wednesday" in decision.reasons[0]
    assert "BYDAY=MO" in decision.reasons[0]


def test_an_off_interval_is_counted_in_periods():
    decision = decide(
        "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO", datetime(2026, 1, 5, 9, 0), datetime(2026, 1, 12, 9, 0)
    )
    assert not decision.occurrence
    assert "1 period(s) from the start" in decision.reasons[0]


def test_a_date_before_the_start_never_fires():
    decision = decide("FREQ=DAILY", datetime(2026, 1, 5, 9, 0), datetime(2026, 1, 4, 9, 0))
    assert not decision.occurrence
    assert "before the start" in decision.reasons[0]


def test_the_spring_gap_explains_itself():
    decision = decide("FREQ=DAILY", datetime(2026, 3, 6, 2, 30), datetime(2026, 3, 8, 2, 30))
    assert not decision.occurrence
    assert "gap the zone made" in decision.reasons[0]


def test_until_explains_the_boundary_it_stopped_at():
    karachi = ZoneInfo("Asia/Kolkata")
    decision = decide(
        "FREQ=DAILY;UNTIL=20260303T033000Z",
        datetime(2026, 3, 1, 9, 0),
        datetime(2026, 3, 4, 9, 0),
        karachi,
    )
    assert not decision.occurrence
    assert "past UNTIL" in decision.reasons[0]


def test_the_last_friday_that_is_fifth_in_its_month_still_explains():
    decision = decide(
        "FREQ=MONTHLY;BYDAY=-1FR", datetime(2026, 1, 1, 9, 0), datetime(2026, 5, 29, 9, 0)
    )
    assert decision.occurrence


def test_a_day_that_is_not_the_last_of_its_weekday_is_refused():
    decision = decide(
        "FREQ=MONTHLY;BYDAY=-1FR", datetime(2026, 1, 1, 9, 0), datetime(2026, 1, 23, 9, 0)
    )
    assert not decision.occurrence
    assert "matches none of BYDAY=-1FR" in decision.reasons[0]


def test_the_lines_name_the_time_and_the_verdict():
    decision = decide("FREQ=DAILY", datetime(2026, 1, 5, 9, 0), datetime(2026, 1, 6, 9, 0))
    lines = decision.lines()
    assert lines[0] == "at         2026-01-06 09:00:00"
    assert lines[1] == "verdict    an occurrence"

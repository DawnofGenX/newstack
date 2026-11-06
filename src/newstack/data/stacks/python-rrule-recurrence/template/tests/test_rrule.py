"""The rule parser is the first gate: an impossible rule never reaches expansion."""

import pytest

from {{ package_name }} import rrule as subject


def test_a_plain_rule_defaults_to_every_period():
    rule = subject.parse("FREQ=DAILY")
    assert rule.freq == "DAILY"
    assert rule.interval == 1
    assert rule.count is None
    assert rule.bounded == "unbounded"


def test_the_prefix_is_optional_and_case_insensitive():
    assert subject.parse("RRULE:FREQ=daily").freq == "DAILY"


def test_unknown_keys_are_named_not_ignored():
    with pytest.raises(subject.RuleError, match="BYHOUR"):
        subject.parse("FREQ=DAILY;BYHOUR=9")


def test_a_missing_frequency_is_refused():
    with pytest.raises(subject.RuleError, match="FREQ is required"):
        subject.parse("COUNT=3")


def test_count_and_until_are_two_endings():
    with pytest.raises(subject.RuleError, match="two different endings"):
        subject.parse("FREQ=DAILY;COUNT=2;UNTIL=20260303T033000Z")


def test_until_without_an_offset_is_a_wall_time():
    with pytest.raises(subject.RuleError, match="instant without an offset"):
        subject.parse("FREQ=DAILY;UNTIL=20260303T033000")


def test_until_z_is_read_as_utc():
    rule = subject.parse("FREQ=DAILY;UNTIL=20260303T033000Z")
    assert rule.until.isoformat() == "2026-03-03T03:30:00+00:00"


def test_an_offset_until_is_converted_to_utc():
    rule = subject.parse("FREQ=DAILY;UNTIL=20260303T090000+05:30")
    assert rule.until.hour == 3 and rule.until.minute == 30


def test_zero_interval_would_stand_still():
    with pytest.raises(subject.RuleError, match="step backwards or stand still"):
        subject.parse("FREQ=DAILY;INTERVAL=0")


def test_a_zero_count_asks_for_nothing():
    with pytest.raises(subject.RuleError, match="no occurrences"):
        subject.parse("FREQ=DAILY;COUNT=0")


def test_ordinals_only_make_sense_inside_a_month():
    with pytest.raises(subject.RuleError, match="no month to count in"):
        subject.parse("FREQ=WEEKLY;BYDAY=1MO")


def test_byday_with_only_a_sign_is_refused():
    with pytest.raises(subject.RuleError, match="sign but no ordinal"):
        subject.parse("FREQ=MONTHLY;BYDAY=+MO")


def test_an_ordinal_past_five_cannot_exist():
    with pytest.raises(subject.RuleError, match="past the fifth weekday"):
        subject.parse("FREQ=MONTHLY;BYDAY=6MO")


def test_byday_duplicates_are_refused():
    with pytest.raises(subject.RuleError, match="twice"):
        subject.parse("FREQ=WEEKLY;BYDAY=MO,MO")


def test_bymonthday_on_a_weekly_rule_is_refused():
    with pytest.raises(subject.RuleError, match="days the week does not choose"):
        subject.parse("FREQ=WEEKLY;BYMONTHDAY=1")


def test_an_impossible_month_day_pair_is_refused_at_parse_time():
    with pytest.raises(subject.RuleError, match="no real date"):
        subject.parse("FREQ=YEARLY;BYMONTH=2,4,6;BYMONTHDAY=31")


def test_february_29_is_a_real_date_so_the_rule_parses():
    rule = subject.parse("FREQ=YEARLY;BYMONTH=2;BYMONTHDAY=29")
    assert rule.bymonthday == (29,)


def test_byday_entries_render_with_their_ordinal():
    rule = subject.parse("FREQ=MONTHLY;BYDAY=-1FR,1MO")
    assert [entry.text for entry in rule.byday] == ["-1FR", "1MO"]


def test_wkst_changes_only_the_week_anchor():
    rule = subject.parse("FREQ=WEEKLY;BYDAY=SU;WKST=SU")
    assert rule.wkst == 6
    assert any(line.startswith("wkst") for line in rule.lines())

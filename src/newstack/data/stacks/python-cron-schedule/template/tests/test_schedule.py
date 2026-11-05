from datetime import UTC, datetime
from itertools import pairwise

import pytest

from {{ package_name }} import model as subject


def moment(text):
    from datetime import datetime

    return datetime.fromisoformat(text).astimezone(UTC)


def test_five_fields_or_nothing():
    schedule = subject.parse("0 9 * * mon-fri")
    assert schedule.expression == "0 9 * * mon-fri"
    assert schedule.minute.values == {0}
    assert schedule.hour.values == {9}
    assert schedule.day.star and schedule.month.star


@pytest.mark.parametrize("text", ["* * * *", "* * * * * *", "", "   ", "0 9 * * funday"])
def test_a_schedule_that_is_not_five_fields(text):
    with pytest.raises(subject.CronError):
        subject.parse(text)


def test_one_restricted_day_field_means_and():
    schedule = subject.parse("0 9 1 * *")
    assert schedule.day_rule == "and"
    assert schedule.matches(moment("2026-03-01T09:00:00+00:00"))
    assert not schedule.matches(moment("2026-03-02T09:00:00+00:00"))


def test_two_restricted_day_fields_mean_or():
    schedule = subject.parse("0 0 1 * 1")
    assert schedule.day_rule == "or"
    # 2026-04-01 is a Wednesday: it matches because it is the 1st.
    assert schedule.matches(moment("2026-04-01T00:00:00+00:00"))
    # 2026-03-09 is a Monday: it matches because it is a Monday.
    assert schedule.matches(moment("2026-03-09T00:00:00+00:00"))
    assert not schedule.matches(moment("2026-03-10T00:00:00+00:00"))


def test_the_hour_and_minute_still_have_to_agree():
    schedule = subject.parse("30 4 1 * *")
    assert not schedule.matches(moment("2026-03-01T04:00:00+00:00"))
    assert schedule.matches(moment("2026-03-01T04:30:00+00:00"))


def test_as_dict_names_every_field():
    payload = subject.parse("*/5 2 1 jan mon").as_dict()
    assert payload["minute"] == "0,5,10,15,20,25,30,35,40,45,50,55"
    assert payload["hour"] == "2"
    assert payload["month"] == "1"
    assert payload["weekday"] == "1"
    assert payload["day_rule"] == "or"


def test_a_run_exactly_at_after_is_not_returned():
    schedule = subject.parse("*/15 * * * *")
    runs = subject.runs_after(schedule, moment("2026-03-07T12:15:00+00:00"), "UTC", count=1)
    assert runs[0].utc.hour == 12 and runs[0].utc.minute == 30


def test_runs_are_strictly_increasing():
    schedule = subject.parse("*/7 * * * *")
    runs = subject.runs_after(schedule, moment("2026-03-07T12:00:00+00:00"), "UTC", count=5)
    assert all(a.utc < b.utc for a, b in pairwise(runs))


def test_a_naive_moment_is_refused():
    naive = datetime(2026, 3, 7, 12, 0)
    with pytest.raises(subject.CronError, match="must carry an offset"):
        subject.runs_after(subject.parse("* * * * *"), naive, "UTC")


def test_something_that_is_not_a_moment_at_all_is_refused():
    with pytest.raises(subject.CronError, match="expected a datetime"):
        subject.runs_after(subject.parse("* * * * *"), "2026-03-07T12:00:00Z", "UTC")


@pytest.mark.parametrize("count", [0, -1])
def test_count_has_to_be_a_real_count(count):
    with pytest.raises(subject.CronError, match="count must be at least 1"):
        subject.runs_after(
            subject.parse("* * * * *"), moment("2026-03-07T12:00:00+00:00"), "UTC", count=count
        )


def test_an_unknown_zone_is_refused_loudly():
    with pytest.raises(subject.CronError, match="unknown time zone"):
        subject.runs_after(
            subject.parse("* * * * *"), moment("2026-03-07T12:00:00+00:00"), "Mars/Olympus"
        )


def test_a_date_that_never_come_returns_nothing():
    runs = subject.runs_after(
        subject.parse("0 0 30 2 *"), moment("2026-03-07T12:00:00+00:00"), "UTC", count=1
    )
    assert runs == []


def test_the_day_skip_does_not_skip_a_valid_run():
    # 00:00 on the 1st is the first minute of a day, the boundary the skip lands on.
    runs = subject.runs_after(
        subject.parse("0 0 1 * *"), moment("2026-03-02T12:00:00+00:00"), "UTC", count=2
    )
    assert [run.utc.date().isoformat() for run in runs] == ["2026-04-01", "2026-05-01"]

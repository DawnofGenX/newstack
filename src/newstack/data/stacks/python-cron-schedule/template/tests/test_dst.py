from datetime import UTC, datetime
from itertools import pairwise

from {{ package_name }} import model as subject

NEW_YORK = "America/New_York"
LONDON = "Europe/London"


def moment(text):
    return datetime.fromisoformat(text).astimezone(UTC)


def test_the_hour_that_does_not_exist_is_skipped():
    schedule = subject.parse("30 2 * * *")
    runs = subject.runs_after(schedule, moment("2026-03-07T12:00:00+00:00"), NEW_YORK, count=2)
    assert runs[0].utc.date().isoformat() == "2026-03-09"
    assert f"{runs[0].local:%H:%M}" == "02:30"
    assert runs[0].local.utcoffset().total_seconds() == -4 * 3600


def test_the_gap_across_the_change_is_47_hours():
    schedule = subject.parse("30 2 * * *")
    before = subject.first_after(schedule, moment("2026-03-06T12:00:00+00:00"), NEW_YORK)
    after = subject.first_after(schedule, moment("2026-03-07T12:00:00+00:00"), NEW_YORK)
    assert before.utc.date().isoformat() == "2026-03-07"
    assert after.utc.date().isoformat() == "2026-03-09"
    assert int((after.utc - before.utc).total_seconds() // 3600) == 47


def test_an_hourly_schedule_loses_one_run_that_night():
    hourly = subject.parse("0 * * * *")
    before = subject.first_after(hourly, moment("2026-03-08T05:00:00+00:00"), NEW_YORK)
    after = subject.first_after(hourly, moment("2026-03-08T06:00:00+00:00"), NEW_YORK)
    assert before.local.hour == 0 or f"{before.utc:%H:%M}" == "06:00"
    assert f"{after.utc:%H:%M}" == "07:00"
    assert f"{after.local:%H:%M}" == "03:00"


def test_the_hour_that_happens_twice_runs_twice():
    schedule = subject.parse("30 1 * * *")
    runs = subject.runs_after(schedule, moment("2026-10-31T12:00:00+00:00"), NEW_YORK, count=3)
    assert [run.utc.date().isoformat() for run in runs[:2]] == ["2026-11-01", "2026-11-01"]
    assert f"{runs[0].local:%H:%M}" == f"{runs[1].local:%H:%M}" == "01:30"
    assert runs[0].local.utcoffset().total_seconds() == -4 * 3600
    assert runs[1].local.utcoffset().total_seconds() == -5 * 3600
    assert int((runs[1].utc - runs[0].utc).total_seconds()) == 3600
    assert runs[2].utc.date().isoformat() == "2026-11-02"


def test_the_uk_spring_change_behaves_the_same_way():
    schedule = subject.parse("30 1 * * *")
    runs = subject.runs_after(schedule, moment("2026-03-28T12:00:00+00:00"), LONDON, count=1)
    assert runs[0].utc.date().isoformat() == "2026-03-30"
    assert f"{runs[0].local:%H:%M}" == "01:30"


def test_the_uk_fall_change_repeats_the_hour():
    schedule = subject.parse("30 1 * * *")
    runs = subject.runs_after(schedule, moment("2026-10-24T12:00:00+00:00"), LONDON, count=2)
    assert [run.utc.date().isoformat() for run in runs] == ["2026-10-25", "2026-10-25"]
    assert int((runs[1].utc - runs[0].utc).total_seconds()) == 3600


def test_utc_never_notices():
    schedule = subject.parse("30 2 * * *")
    runs = subject.runs_after(schedule, moment("2026-03-07T12:00:00+00:00"), "UTC", count=3)
    assert [f"{run.utc:%m-%d %H:%M}" for run in runs] == [
        "03-08 02:30",
        "03-09 02:30",
        "03-10 02:30",
    ]


def test_a_daily_midnight_job_across_the_fall_change():
    # Local midnight is not 24 hours away from the previous one on that night.
    schedule = subject.parse("0 0 * * *")
    runs = subject.runs_after(schedule, moment("2026-10-30T12:00:00+00:00"), NEW_YORK, count=3)
    gaps = [int((b.utc - a.utc).total_seconds() // 3600) for a, b in pairwise(runs)]
    assert gaps == [24, 25]
